from datetime import datetime, timedelta,time
from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from reservations.models import Reservation, ReservationCoach, Terrain,Coach,Schedule
from core.models import User
from reservations import views
#from rest_framework.response import Response
#from rest_framework.decorators import api_view
@csrf_exempt
def list_terrains(request):
    terrains = Terrain.objects.all().values('id', 'name', 'location', 'price_per_hour', 'available')
    return JsonResponse(list(terrains), safe=False)


#@api_view(['GET'])
#def get    Terrain(request):
    #terrains = Terrain.objects.all().values()
    #return Response(terrains)


#@api_view(['GET'])
#def getTerrainbyid(request, terrain_id):
    #terrains = Terrain.objects.all().values()
    #return Response(terrains,terrain_id)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_terrain_by_id(request, terrain_id):
    terrain = get_object_or_404(Terrain, id=terrain_id)
    return JsonResponse({
        'id': terrain.id,
        'name': terrain.name,
        'location': terrain.location,
        'price_per_hour': str(terrain.price_per_hour)
    })

def is_admin(user):
    return user.role == 'admin'
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_terrain(request):
    user = request.user  # Get the logged-in user
    if not is_admin(user):
        return JsonResponse({'error': 'You are not authorized to perform this action.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        terrain = Terrain.objects.create(
            name=data['name'],
            location=data['location'],
            price_per_hour=Decimal(data['price_per_hour'])
        )
        return JsonResponse({'message': 'Terrain added successfully', 'terrain_id': terrain.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_terrain(request, terrain_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'You are not authorized to perform this action.'}, status=403)

    terrain = get_object_or_404(Terrain, id=terrain_id)
    terrain.delete()
    return JsonResponse({'message': 'Terrain deleted successfully'})



@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_terrain(request, terrain_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'You are not authorized to perform this action.'}, status=403)

    if request.method == 'PUT':
        data = json.loads(request.body)
        terrain = get_object_or_404(Terrain, id=terrain_id)
        
        terrain.name = data.get('name', terrain.name)
        terrain.location = data.get('location', terrain.location)
        terrain.price_per_hour = Decimal(data.get('price_per_hour', terrain.price_per_hour))
        
        terrain.save()
        return JsonResponse({'message': 'Terrain updated successfully'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])  # 👈 This is critical
def make_reservation(request):
    data = request.data

    try:
        terrain = Terrain.objects.get(id=data['terrain_id'])
    except Terrain.DoesNotExist:
        return JsonResponse({'error': 'Terrain not found.'}, status=404)

    start_time = data['start_time']
    end_time = data['end_time']

    start_time_obj = timedelta(hours=int(start_time.split(":")[0]), minutes=int(start_time.split(":")[1]))
    end_time_obj = timedelta(hours=int(end_time.split(":")[0]), minutes=int(end_time.split(":")[1]))

    duration = (end_time_obj - start_time_obj).seconds / 3600
    if duration < 1:
        duration = 1
    duration = Decimal(duration)

    total_price = duration * terrain.price_per_hour

    user = request.user if request.user.is_authenticated else None

    reservation = Reservation.objects.create(
        user=user,
        terrain=terrain,
        date=data['date'],
        start_time=start_time,
        end_time=end_time
    )

    return JsonResponse({
        'message': 'Reservation created successfully',
        'reservation': {
            'user': user.username if user else 'Anonymous',
            'terrain': terrain.name,
            'date': data['date'],
            'start_time': start_time,
            'end_time': end_time,
            'total_price': str(total_price)
        }
    })

@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_reservation(request, reservation_id):
    user = request.user
    if not hasattr(user, 'role') or user.role.lower() != 'joueur':
        return JsonResponse({'error': 'Only players can update reservations.'}, status=403)

    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return JsonResponse({'error': 'Reservation not found.'}, status=404)

    # Anonymous reservations cannot be updated
    if reservation.user is None:
        return JsonResponse({'error': 'Anonymous reservations cannot be updated.'}, status=403)

    if reservation.user != user:
        return JsonResponse({'error': 'You are not allowed to update this reservation.'}, status=403)

    data = json.loads(request.body)
    try:
        terrain = Terrain.objects.get(id=data['terrain_id'])
    except Terrain.DoesNotExist:
        return JsonResponse({'error': 'Terrain not found.'}, status=404)

    reservation.terrain = terrain
    reservation.date = data['date']
    reservation.start_time = data['start_time']
    reservation.end_time = data['end_time']
    reservation.save()

    return JsonResponse({'message': 'Reservation updated successfully'})


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_reservation(request, reservation_id):
    user = request.user
    if not hasattr(user, 'role') or user.role.lower() != 'joueur':
        return JsonResponse({'error': 'Only players can delete reservations.'}, status=403)

    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return JsonResponse({'error': 'Reservation not found.'}, status=404)

    # Anonymous reservations cannot be deleted
    if reservation.user is None:
        return JsonResponse({'error': 'Anonymous reservations cannot be deleted.'}, status=403)

    if reservation.user != user:
        return JsonResponse({'error': 'You are not allowed to delete this reservation.'}, status=403)

    reservation.delete()
    return JsonResponse({'message': 'Reservation deleted successfully'}, status=204)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_reservations(request):
    user = request.user

    if not hasattr(user, 'role') or user.role.lower() != 'joueur':
        return JsonResponse({'error': 'Only players can view their reservations.'}, status=403)

    # Récupère toutes les réservations de l'utilisateur
    reservations = Reservation.objects.filter(user=user)

    if not reservations:
        return JsonResponse({'message': 'No reservations found for this user.'}, status=404)

    # Format des réservations à renvoyer
    reservation_list = []
    for reservation in reservations:
        reservation_list.append({
            'id': reservation.id,
            'terrain': reservation.terrain.name,
            'date': reservation.date,
            'start_time': reservation.start_time,
            'end_time': reservation.end_time,
        })

    return JsonResponse({'reservations': reservation_list}, status=200)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_all_coaches(request):
    try:
        coaches = Coach.objects.all().values(
            "id", "name", "price_per_hour", "phone", "email", "experience"
        )
        return JsonResponse(list(coaches), safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


def is_coach(user):
    return user.role == 'coach'



@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def create_or_update_schedule(request):
    user = request.user

    # Check if the user is an admin (can control other coaches' schedules)
    if user.role != 'admin':  # Ensure the user is an admin
        return Response({"error": "Authenticated user is not an admin."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the coach_id from the request data (this will be provided by the admin)
    coach_id = request.data.get('coach_id')  # Ensure the admin specifies which coach's schedule to modify

    if not coach_id:
        return Response({"error": "Coach ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        coach = Coach.objects.get(id=coach_id)  # Get the coach by ID
    except Coach.DoesNotExist:
        return Response({"error": "Coach not found."}, status=status.HTTP_404_NOT_FOUND)

    # Parse the schedule data from the request
    schedule_data = request.data.get('schedule', [])

    if not schedule_data:
        return Response({"error": "No schedule data provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Iterate over the provided schedule data and save or update the schedule for the specified coach
    for item in schedule_data:
        date = item.get('date')
        start_time = item.get('start_time')
        end_time = item.get('end_time')

        if not date or not start_time or not end_time:
            return Response({"error": "Invalid schedule data provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Create or update the schedule entry for the specified coach
        schedule, created = Schedule.objects.update_or_create(
            coach=coach,  # Use the specified coach
            date=date,
            start_time=start_time,
            end_time=end_time,
            defaults={'is_booked': False}  # You can add more default values if needed
        )

    return Response({"status": "success", "message": "Schedule has been updated/created successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def check_coach_availability(request, coach_id, date):
    try:
        # Ensure the coach exists
        coach = get_object_or_404(Coach, id=coach_id)

        schedules = Schedule.objects.filter(
            coach=coach,
            date=date,
            is_booked=False
        ).values("start_time", "end_time")

        return JsonResponse({"available_times": list(schedules)}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def make_coach_reservation(request, coach_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = get_object_or_404(User, id=data['user_id'])
            coach = get_object_or_404(Coach, id=coach_id)
            date = data['date']
            
          
            try:
                requested_start_time = datetime.strptime(data['start_time'], "%H:%M").time()
                requested_end_time = datetime.strptime(data['end_time'], "%H:%M").time()
            except ValueError as e:
                return JsonResponse({'error': f'Invalid time format: {str(e)}'}, status=400)

           
            min_time = time(6, 0)
            max_time = time(18, 0)

           
            if not (min_time <= requested_start_time < max_time and min_time < requested_end_time <= max_time):
                return JsonResponse({'error': 'Reservations are only allowed between 06:00 and 18:00.'}, status=400)

            available_schedule = Schedule.objects.filter(
                coach=coach,
                date=date,
                start_time__lte=requested_start_time,
                end_time__gte=requested_end_time,
                is_booked=False
            ).first()

            if not available_schedule:
                return JsonResponse({'error': 'Coach is not available at this time.'}, status=400)

          
            available_schedule.is_booked = True
            available_schedule.save()

           
            duration = max(
                (requested_end_time.hour + requested_end_time.minute / 60) -
                (requested_start_time.hour + requested_start_time.minute / 60),
                1
            )
            total_price = Decimal(duration) * coach.price_per_hour

            # Create reservation
            reservation = ReservationCoach.objects.create(
                user=user,
                coach=coach,
                date=date,
                start_time=requested_start_time,
                end_time=requested_end_time,
                total_price=total_price
            )

            return JsonResponse({
                'message': 'Reservation created successfully',
                'reservation': {
                    'user': user.username,
                    'coach': coach.name,
                    'date': date,
                    'start_time': str(requested_start_time),
                    'end_time': str(requested_end_time),
                    'total_price': str(total_price)
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def update_coach_reservation(request, reservation_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            reservation = get_object_or_404(ReservationCoach, id=reservation_id)

            # Get new values
            date = data.get('date', reservation.date)
            start_time_str = data.get('start_time', str(reservation.start_time))
            end_time_str = data.get('end_time', str(reservation.end_time))

            # Convert string times to time objects
            try:
                new_start_time = datetime.strptime(start_time_str, "%H:%M").time()
                new_end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except ValueError as e:
                return JsonResponse({'error': f'Invalid time format: {str(e)}'}, status=400)

            # Ensure new time is within allowed hours
            min_time, max_time = time(6, 0), time(18, 0)
            if not (min_time <= new_start_time < max_time and min_time < new_end_time <= max_time):
                return JsonResponse({'error': 'Reservations are only allowed between 06:00 and 18:00.'}, status=400)

            # Check if the new time slot is available
            existing_schedule = Schedule.objects.filter(
                coach=reservation.coach,
                date=date,
                start_time__lte=new_start_time,
                end_time__gte=new_end_time,
                is_booked=False
            ).first()

            if not existing_schedule:
                return JsonResponse({'error': 'The new time slot is unavailable.'}, status=400)

            # Release old schedule and book new one
            old_schedule = Schedule.objects.filter(
                coach=reservation.coach,
                date=reservation.date,
                start_time__lte=reservation.start_time,
                end_time__gte=reservation.end_time
            ).first()
            if old_schedule:
                old_schedule.is_booked = False
                old_schedule.save()

            existing_schedule.is_booked = True
            existing_schedule.save()

            # Update reservation details
            reservation.date = date
            reservation.start_time = new_start_time
            reservation.end_time = new_end_time
            reservation.total_price = max((new_end_time.hour + new_end_time.minute / 60) - 
                                          (new_start_time.hour + new_start_time.minute / 60), 1) * reservation.coach.price_per_hour
            reservation.save()

            return JsonResponse({
                'message': 'Reservation updated successfully',
                'reservation': {
                    'user': reservation.user.username,
                    'coach': reservation.coach.name,
                    'date': date,
                    'start_time': str(new_start_time),
                    'end_time': str(new_end_time),
                    'total_price': str(reservation.total_price)
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def delete_coach_reservation(request, reservation_id):
    if request.method == 'DELETE':
        reservation = get_object_or_404(ReservationCoach, id=reservation_id)

        # Release the schedule slot
        schedule = Schedule.objects.filter(
            coach=reservation.coach,
            date=reservation.date,
            start_time__lte=reservation.start_time,
            end_time__gte=reservation.end_time
        ).first()

        if schedule:
            schedule.is_booked = False
            schedule.save()

        reservation.delete()
        return JsonResponse({'message': 'Reservation deleted successfully'})

    return JsonResponse({'error': 'Invalid request'}, status=400)



@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_coach(request):
    user = request.user  
    if not is_admin(user):
        return JsonResponse({'error': 'You are not authorized to perform this action.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)

     
        required_fields = ['name',  'price_per_hour', 'phone', 'email', 'experience']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

        try:
            coach = Coach.objects.create(
                name=data['name'],
                price_per_hour=Decimal(data['price_per_hour']),
                phone=data['phone'],
                email=data['email'],
                experience=data['experience']
            )
            return JsonResponse({'message': 'Coach added successfully', 'coach_id': coach.id})
        except Exception as e:
            return JsonResponse({'error': f'Error creating coach: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

from rest_framework.response import Response
from rest_framework import status

@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_coach(request, coach_id):
    user = request.user  
    if not is_admin(user):
        return JsonResponse({'error': 'You are not authorized to perform this action.'}, status=403)

    try:
        coach = Coach.objects.get(id=coach_id)
        coach.delete()
        return Response({'message': 'Coach deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    except Coach.DoesNotExist:
        return Response({'error': 'Coach not found'}, status=status.HTTP_404_NOT_FOUND)
    



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_player_coach_reservations(request):
    user = request.user

    # Verify if the user is a player
    if not hasattr(user, 'role') or user.role.lower() != 'joueur':
        return JsonResponse({'error': 'Only players can view their coach reservations.'}, status=403)

    # Retrieve all coach reservations for the current player
    reservations = ReservationCoach.objects.filter(user=user)

    if not reservations:
        return JsonResponse({'message': 'No coach reservations found for this player.'}, status=404)

    # Format reservations to return in the response
    reservation_list = []
    for reservation in reservations:
        reservation_list.append({
            'id': reservation.id,
            'coach': reservation.coach.name,
            'date': reservation.date,
            'start_time': reservation.start_time,
            'end_time': reservation.end_time,
            'total_price': str(reservation.total_price),
        })

    return JsonResponse({'reservations': reservation_list}, status=200)
def nav(request):
    return render(request, 'html/navbar.html')


def footer(request):
    return render(request, 'html/footer.html')



def home(request):
    return render(request, 'html/home.html')


def base(request):
    return render(request, 'html/base.html')

def reservation(request):
    return render(request, 'html/reservation.html')