from datetime import datetime, timedelta,time
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from reservations.models import CustomUser, Reservation, ReservationCoach, Terrain,Coach,Schedule
#from rest_framework.response import Response
#from rest_framework.decorators import api_view
@csrf_exempt
def list_terrains(request):
    terrains = Terrain.objects.all().values()
    return JsonResponse(list(terrains), safe=False)


#@api_view(['GET'])
#def get    Terrain(request):
    #terrains = Terrain.objects.all().values()
    #return Response(terrains)


#@api_view(['GET'])
#def getTerrainbyid(request, terrain_id):
    #terrains = Terrain.objects.all().values()
    #return Response(terrains,terrain_id)

@csrf_exempt
def get_terrain_by_id(request, terrain_id):
    terrain = get_object_or_404(Terrain, id=terrain_id)
    return JsonResponse({
        'id': terrain.id,
        'name': terrain.name,
        'location': terrain.location,
        'price_per_hour': str(terrain.price_per_hour)
    })

@csrf_exempt
def add_terrain(request):
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
def delete_terrain(request, terrain_id):
    terrain = get_object_or_404(Terrain, id=terrain_id)
    terrain.delete()
    return JsonResponse({'message': 'Terrain deleted successfully'})

@csrf_exempt
def update_terrain(request, terrain_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        terrain = get_object_or_404(Terrain, id=terrain_id)
        
        terrain.name = data.get('name', terrain.name)
        terrain.location = data.get('location', terrain.location)
        terrain.price_per_hour = Decimal(data.get('price_per_hour', terrain.price_per_hour))
        
        terrain.save()
        return JsonResponse({'message': 'Terrain updated successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def make_reservation(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        user = CustomUser.objects.get(id=data['user_id'])
        terrain = Terrain.objects.get(id=data['terrain_id'])
        
        start_time = data['start_time']
        end_time = data['end_time']
        
        start_time_obj = timedelta(hours=int(start_time.split(":")[0]), minutes=int(start_time.split(":")[1]))
        end_time_obj = timedelta(hours=int(end_time.split(":")[0]), minutes=int(end_time.split(":")[1]))
        
        duration = (end_time_obj - start_time_obj).seconds / 3600
        if duration < 1:
            duration = 1
        duration = Decimal(duration)
        
        total_price = duration * terrain.price_per_hour
        
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
                'user': user.username,
                'terrain': terrain.name,
                'date': data['date'],
                'start_time': start_time,
                'end_time': end_time,
                'total_price': total_price
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_all_coaches(request):
    coaches = Coach.objects.all().values("id", "name", "specialty", "price_per_hour", "phone", "email", "experience_years")
    return JsonResponse(list(coaches), safe=False)

def check_coach_availability(request, coach_id, date):
    schedules = Schedule.objects.filter(coach_id=coach_id, date=date, is_booked=False).values("start_time", "end_time")
    return JsonResponse({"available_times": list(schedules)})



@csrf_exempt
def make_coach_reservation(request, coach_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = get_object_or_404(CustomUser, id=data['user_id'])
            coach = get_object_or_404(Coach, id=coach_id)
            date = data['date']
            
            # Convert string times to Python time objects
            try:
                requested_start_time = datetime.strptime(data['start_time'], "%H:%M").time()
                requested_end_time = datetime.strptime(data['end_time'], "%H:%M").time()
            except ValueError as e:
                return JsonResponse({'error': f'Invalid time format: {str(e)}'}, status=400)

            # Define allowed reservation interval (6 AM to 6 PM)
            min_time = time(6, 0)
            max_time = time(18, 0)

            # Ensure reservation is within allowed hours
            if not (min_time <= requested_start_time < max_time and min_time < requested_end_time <= max_time):
                return JsonResponse({'error': 'Reservations are only allowed between 06:00 and 18:00.'}, status=400)

            # Check if requested time fits within an available schedule
            available_schedule = Schedule.objects.filter(
                coach=coach,
                date=date,
                start_time__lte=requested_start_time,
                end_time__gte=requested_end_time,
                is_booked=False
            ).first()

            if not available_schedule:
                return JsonResponse({'error': 'Coach is not available at this time.'}, status=400)

            # Mark the schedule as booked
            available_schedule.is_booked = True
            available_schedule.save()

            # Calculate duration & total price
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
