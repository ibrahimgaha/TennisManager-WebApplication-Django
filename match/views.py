from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Match
from .serializers import MatchSerializer

User = get_user_model()


# ✅ List all matches or create a new one
#GET: List all matches
#POST: Create a match (requires token)
class MatchListCreateView(generics.ListCreateAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Match.objects.all().order_by('-created_at')

        match_type = self.request.query_params.get('type')
        location = self.request.query_params.get('location')

        if match_type:
            queryset = queryset.filter(match_type=match_type)
        if location:
            queryset = queryset.filter(location__icontains=location)

        return queryset

    def perform_create(self, serializer):
        # Automatically sets the match creator to the logged-in user
        serializer.save(created_by=self.request.user)


# ✅ Join a match if you're not the creator or already joined
# PUT (requires token)
class JoinMatchView(generics.UpdateAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        match = self.get_object()

        if match.opponent:
            return Response({"error": "Match already has an opponent."}, status=status.HTTP_400_BAD_REQUEST)

        if match.created_by == request.user:
            return Response({"error": "You cannot join your own match."}, status=status.HTTP_400_BAD_REQUEST)

        match.opponent = request.user
        match.is_confirmed = True
        match.save()

        serializer = self.get_serializer(match)
        return Response(serializer.data)


# ✅ Search for matches by user name or email
#GET (requires token)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def find_matches_by_user(request):
    query = request.query_params.get('q')
    if not query:
        return Response({"error": "You must provide a search query."}, status=400)

    users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query))
    matches = Match.objects.filter(Q(created_by__in=users) | Q(opponent__in=users)).order_by('-created_at')

    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)
