import json
import os
from django.conf import settings
from rest_framework import generics
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import User
import face_recognition
from django.core.files.storage import default_storage
from django.shortcuts import render

# JWT imports
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

def home_view(request):
    return render(request, 'html/home.html')

def login_view(request):
    return render(request, 'html/login.html')

def register_view(request):
    return render(request, 'html/register.html')

def coach_dashboard_view(request):
    return render(request, 'html/coach_dashboard.html')

def joueur_dashboard_view(request):
    return render(request, 'html/joueur_dashboard.html')

def admin_dashboard_view(request):
    return render(request, 'html/admin_dashboard.html')

def abonne_dashboard_view(request):
    return render(request, 'html/abonne_dashboard.html')

User = get_user_model()
#nrml login and register function
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
#face recognition login and register function
class FaceLoginView(APIView):
    parser_classes = [MultiPartParser, FormParser]  # This allows file uploads

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        face_image = request.FILES.get('face_image')  # Get the image from the request

        if not email or not password or not face_image:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize image path variable
        image_path = None
        absolute_image_path = None

        try:
            # Save the uploaded image temporarily using the default storage system
            image_path = default_storage.save('temp_image.jpg', face_image)
            absolute_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

            uploaded_image = face_recognition.load_image_file(absolute_image_path)
            uploaded_face_encoding = face_recognition.face_encodings(uploaded_image)

            if len(uploaded_face_encoding) == 0:
                return Response({"error": "No face found in the image"}, status=status.HTTP_400_BAD_REQUEST)

            uploaded_face_encoding = uploaded_face_encoding[0]  # Use the first face encoding found

            # Get user by email
            user = User.objects.get(email=email)

            # Check password
            if not user.check_password(password):
                return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

            # Deserialize the saved face encoding
            saved_face_encoding = json.loads(user.face_encoding)

            # Compare the face encoding (use a matching threshold if necessary)
            if face_recognition.compare_faces([saved_face_encoding], uploaded_face_encoding)[0]:
                # If face matches, authenticate user
                return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Face not recognized"}, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clean up the temporary image if it was saved
            if absolute_image_path and os.path.exists(absolute_image_path):
                os.remove(absolute_image_path)

class RegisterFaceLoginView(APIView):
    parser_classes = [MultiPartParser, FormParser]  # This allows file uploads

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        face_image = request.FILES.get('face_image')  # Get the image from the request

        if not email or not password or not face_image:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Save the uploaded image temporarily
            image_path = default_storage.save('temp_image.jpg', face_image)
            full_image_path = default_storage.path(image_path)

            # Load the image and get the face encoding
            image = face_recognition.load_image_file(full_image_path)
            face_encoding = face_recognition.face_encodings(image)

            if len(face_encoding) == 0:
                return Response({"error": "No face found in the image"}, status=status.HTTP_400_BAD_REQUEST)

            face_encoding = face_encoding[0]  # Use the first face encoding found

            # Use the email as the username or provide a default username
            username = email.split('@')[0]  # Use the part before '@' as a default username

            # Create the user and store the face encoding
            user = User.objects.create_user(username=username, email=email, password=password,role='joueur')  # Now including username
            user.face_encoding = json.dumps(face_encoding.tolist())  # Save face encoding as JSON string
            user.save()

            # Clean up the temporary image
            if os.path.exists(full_image_path):
                os.remove(full_image_path)

            return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Clean up the temporary image if an error occurs
            if os.path.exists(full_image_path):
                os.remove(full_image_path)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CoachListView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve all users with the role 'coach'
        coaches = User.objects.filter(role='coach')

        # If no coaches found, return a 404 response
        if not coaches.exists():
            return Response({"message": "No coaches found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a list of coaches with desired data (e.g., username and email)
        coach_data = [{"username": coach.username, "email": coach.email} for coach in coaches]

        return Response(coach_data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile information"""
        user = request.user
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'avatar': user.avatar.url if user.avatar else None,
        }
        return Response(user_data, status=status.HTTP_200_OK)


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Subscribe a player to become a subscriber"""
        user = request.user
        plan_type = request.data.get('plan_type')

        # Check if user is a player
        if user.role != 'joueur':
            return Response({
                'error': 'Only players can subscribe to premium plans!'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate plan type
        valid_plans = ['basic', 'premium', 'vip']
        if plan_type not in valid_plans:
            return Response({
                'error': 'Invalid plan type. Choose from: basic, premium, vip'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update user role to subscriber
        user.role = 'abonnée'
        user.save()

        return Response({
            'message': f'Successfully subscribed to {plan_type} plan!',
            'new_role': user.role,
            'plan_type': plan_type
        }, status=status.HTTP_200_OK)


# Custom JWT Token Serializer that includes user role
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user information to the response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }
        return data


# Custom Login View that includes user role
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer