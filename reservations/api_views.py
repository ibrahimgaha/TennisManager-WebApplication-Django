from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

from .models import (
    Terrain, Reservation, Coach, ReservationCoach, Schedule, ScheduleSlot,
    Equipment, EquipmentOrder, Subscription, Tournament,
    TournamentRegistration, Notification, Payment
)
from core.models import User


# ==================== TERRAIN MANAGEMENT ====================

@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def terrain_management(request):
    if request.method == 'GET':
        terrains = Terrain.objects.all().values(
            'id', 'name', 'location', 'price_per_hour', 'available'
        )
        return JsonResponse(list(terrains), safe=False)
    
    elif request.method == 'POST':
        # Only admin can create terrains
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Only admins can create terrains'}, status=403)
        
        data = json.loads(request.body)
        terrain = Terrain.objects.create(
            name=data['name'],
            location=data['location'],
            price_per_hour=data['price_per_hour'],
            available=data.get('available', True)
        )
        return JsonResponse({
            'message': 'Terrain created successfully',
            'terrain_id': terrain.id
        })


@api_view(['PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def terrain_detail(request, terrain_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admins can modify terrains'}, status=403)
    
    terrain = get_object_or_404(Terrain, id=terrain_id)
    
    if request.method == 'PUT':
        data = json.loads(request.body)
        terrain.name = data.get('name', terrain.name)
        terrain.location = data.get('location', terrain.location)
        terrain.price_per_hour = data.get('price_per_hour', terrain.price_per_hour)
        terrain.available = data.get('available', terrain.available)
        terrain.save()
        return JsonResponse({'message': 'Terrain updated successfully'})
    
    elif request.method == 'DELETE':
        terrain.delete()
        return JsonResponse({'message': 'Terrain deleted successfully'})


# ==================== RESERVATION MANAGEMENT ====================

@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def court_reservations(request):
    if request.method == 'GET':
        # Get user's reservations
        reservations = Reservation.objects.filter(user=request.user).select_related('terrain')
        reservation_list = []
        for res in reservations:
            reservation_list.append({
                'id': res.id,
                'terrain_name': res.terrain.name,
                'terrain_location': res.terrain.location,
                'date': res.date,
                'start_time': res.start_time,
                'end_time': res.end_time,
                'price': float(res.calculate_price())
            })
        return JsonResponse({'reservations': reservation_list})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['terrain_id', 'date', 'start_time', 'end_time']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

            # Get terrain
            try:
                terrain = Terrain.objects.get(id=data['terrain_id'])
            except Terrain.DoesNotExist:
                return JsonResponse({'error': 'Court not found'}, status=400)

            # Check if terrain is available
            if not terrain.available:
                return JsonResponse({'error': 'Court is not available'}, status=400)

            # Parse date and time
            from datetime import datetime, date, time
            try:
                reservation_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                start_time = datetime.strptime(data['start_time'], '%H:%M').time()
                end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError as e:
                return JsonResponse({'error': f'Invalid date/time format: {str(e)}'}, status=400)

            # Validate time logic
            if start_time >= end_time:
                return JsonResponse({'error': 'Start time must be before end time'}, status=400)

            # Check if date is not in the past
            if reservation_date < date.today():
                return JsonResponse({'error': 'Cannot make reservations for past dates'}, status=400)

            # Check for conflicts
            existing = Reservation.objects.filter(
                terrain=terrain,
                date=reservation_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()

            if existing:
                return JsonResponse({'error': 'Time slot is already booked'}, status=400)

            # Create reservation
            reservation = Reservation.objects.create(
                user=request.user,
                terrain=terrain,
                date=reservation_date,
                start_time=start_time,
                end_time=end_time
            )

            # Create payment record
            price = reservation.calculate_price()
            Payment.objects.create(
                user=request.user,
                payment_type='court_reservation',
                amount=price,
                status='completed',
                transaction_id=f'COURT_{reservation.id}_{int(timezone.now().timestamp())}',
                description=f'Court reservation: {terrain.name} on {reservation_date}'
            )

            # Create notification
            Notification.objects.create(
                user=request.user,
                title='Court Reservation Confirmed',
                message=f'Your reservation for {terrain.name} on {reservation_date} from {start_time} to {end_time} has been confirmed.',
                notification_type='reservation'
            )

            return JsonResponse({
                'message': 'Reservation created successfully',
                'reservation_id': reservation.id,
                'price': float(price),
                'court_name': terrain.name,
                'date': reservation_date.strftime('%Y-%m-%d'),
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M')
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Court reservation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Reservation failed: {str(e)}'}, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Check if user owns the reservation or is admin
    if reservation.user != request.user and request.user.role != 'admin':
        return JsonResponse({'error': 'You can only cancel your own reservations'}, status=403)

    reservation.delete()
    return JsonResponse({'message': 'Reservation cancelled successfully'})


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_court_reservation(request, reservation_id):
    """Update a court reservation"""
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id)

        # Check if user owns the reservation or is admin
        if reservation.user != request.user and request.user.role != 'admin':
            return JsonResponse({'error': 'You can only update your own reservations'}, status=403)

        data = json.loads(request.body)
        new_date = data.get('date')
        new_start_time = data.get('start_time')
        new_end_time = data.get('end_time')

        if not all([new_date, new_start_time, new_end_time]):
            return JsonResponse({'error': 'Date, start time, and end time are required'}, status=400)

        # Parse the data
        try:
            reservation_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            start_time = datetime.strptime(new_start_time, '%H:%M').time()
            end_time = datetime.strptime(new_end_time, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time format'}, status=400)

        # Validate date is not in the past
        if reservation_date < timezone.now().date():
            return JsonResponse({'error': 'Cannot schedule reservation in the past'}, status=400)

        # Validate time range
        if start_time >= end_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

        # Check for conflicts (excluding current reservation)
        existing = Reservation.objects.filter(
            terrain=reservation.terrain,
            date=reservation_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(id=reservation_id).exists()

        if existing:
            return JsonResponse({'error': 'Time slot is already booked'}, status=400)

        # Update the reservation
        reservation.date = reservation_date
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.save()

        return JsonResponse({
            'message': 'Reservation updated successfully',
            'reservation': {
                'id': reservation.id,
                'terrain_name': reservation.terrain.name,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'price': float(reservation.calculate_price())
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cancel_coach_reservation(request, reservation_id):
    """Cancel a coach reservation"""
    try:
        reservation = get_object_or_404(ReservationCoach, id=reservation_id)

        # Check if user owns the reservation or is admin
        if reservation.user != request.user and request.user.role != 'admin':
            return JsonResponse({'error': 'You can only cancel your own reservations'}, status=403)

        reservation.delete()
        return JsonResponse({'message': 'Coach reservation cancelled successfully'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_coach_reservation(request, reservation_id):
    """Update a coach reservation (can change coach, date, and time)"""
    try:
        reservation = get_object_or_404(ReservationCoach, id=reservation_id)

        # Check if user owns the reservation or is admin
        if reservation.user != request.user and request.user.role != 'admin':
            return JsonResponse({'error': 'You can only update your own reservations'}, status=403)

        data = json.loads(request.body)
        new_date = data.get('date')
        new_start_time = data.get('start_time')
        new_end_time = data.get('end_time')
        new_coach_id = data.get('coach_id')  # Optional: change coach

        if not all([new_date, new_start_time, new_end_time]):
            return JsonResponse({'error': 'Date, start time, and end time are required'}, status=400)

        # Parse the data
        try:
            reservation_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            start_time = datetime.strptime(new_start_time, '%H:%M').time()
            end_time = datetime.strptime(new_end_time, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time format'}, status=400)

        # Validate date is not in the past
        if reservation_date < timezone.now().date():
            return JsonResponse({'error': 'Cannot schedule reservation in the past'}, status=400)

        # Validate time range
        if start_time >= end_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

        # Determine which coach to use
        target_coach = reservation.coach  # Default to current coach
        if new_coach_id:
            try:
                target_coach = Coach.objects.get(id=new_coach_id)
            except Coach.DoesNotExist:
                return JsonResponse({'error': 'Selected coach not found'}, status=400)

        # Check for conflicts with target coach's schedule (excluding current reservation)
        existing = ReservationCoach.objects.filter(
            coach=target_coach,
            date=reservation_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(id=reservation_id).exists()

        if existing:
            coach_name = target_coach.name
            return JsonResponse({'error': f'Coach {coach_name} is not available at this time'}, status=400)

        # Update the reservation
        reservation.coach = target_coach
        reservation.date = reservation_date
        reservation.start_time = start_time
        reservation.end_time = end_time

        # Recalculate price based on new duration and coach's rate
        duration_hours = (datetime.combine(reservation_date, end_time) -
                         datetime.combine(reservation_date, start_time)).total_seconds() / 3600
        reservation.total_price = target_coach.price_per_hour * duration_hours

        reservation.save()

        return JsonResponse({
            'message': 'Coach reservation updated successfully',
            'reservation': {
                'id': reservation.id,
                'coach_name': reservation.coach.name,
                'coach_id': reservation.coach.id,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'price': float(reservation.total_price),
                'duration_hours': duration_hours
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== EQUIPMENT MANAGEMENT ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def equipment_list(request):
    equipment = Equipment.objects.filter(available=True).values(
        'id', 'name', 'type', 'brand', 'price', 'stock_quantity', 'description', 'image'
    )
    return JsonResponse({
        'equipment': list(equipment),
        'count': len(equipment)
    })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def order_equipment(request):
    data = json.loads(request.body)
    equipment = get_object_or_404(Equipment, id=data['equipment_id'])
    
    quantity = int(data.get('quantity', 1))
    if equipment.stock_quantity < quantity:
        return JsonResponse({'error': 'Insufficient stock'}, status=400)
    
    order = EquipmentOrder.objects.create(
        user=request.user,
        equipment=equipment,
        quantity=quantity,
        delivery_address=data['delivery_address'],
        notes=data.get('notes', '')
    )
    
    # Update stock
    equipment.stock_quantity -= quantity
    equipment.save()
    
    return JsonResponse({
        'message': 'Order placed successfully',
        'order_id': order.id,
        'total_price': float(order.total_price)
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_orders(request):
    orders = EquipmentOrder.objects.filter(user=request.user).select_related('equipment')
    order_list = []
    for order in orders:
        order_list.append({
            'id': order.id,
            'equipment_name': order.equipment.name,
            'equipment_brand': order.equipment.brand,
            'quantity': order.quantity,
            'total_price': float(order.total_price),
            'status': order.status,
            'order_date': order.order_date,
            'delivery_address': order.delivery_address
        })
    return JsonResponse({'orders': order_list})


# ==================== TOURNAMENT MANAGEMENT ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def tournament_list(request):
    tournaments = Tournament.objects.filter(status__in=['upcoming', 'ongoing']).values(
        'id', 'name', 'description', 'tournament_type', 'start_date', 'end_date',
        'registration_deadline', 'max_participants', 'entry_fee', 'prize_money', 'status'
    )
    return JsonResponse(list(tournaments), safe=False)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def register_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Check if registration is still open
    if tournament.registration_deadline < timezone.now():
        return JsonResponse({'error': 'Registration deadline has passed'}, status=400)
    
    # Check if already registered
    if TournamentRegistration.objects.filter(tournament=tournament, player=request.user).exists():
        return JsonResponse({'error': 'Already registered for this tournament'}, status=400)
    
    # Check if tournament is full
    current_registrations = TournamentRegistration.objects.filter(tournament=tournament).count()
    if current_registrations >= tournament.max_participants:
        return JsonResponse({'error': 'Tournament is full'}, status=400)
    
    registration = TournamentRegistration.objects.create(
        tournament=tournament,
        player=request.user
    )
    
    return JsonResponse({
        'message': 'Successfully registered for tournament',
        'registration_id': registration.id
    })


# ==================== STATISTICS ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    if request.user.role == 'admin':
        # Admin statistics
        total_users = User.objects.count()
        total_terrains = Terrain.objects.count()
        total_coaches = Coach.objects.count()
        total_reservations = Reservation.objects.count()
        total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        return JsonResponse({
            'total_users': total_users,
            'total_terrains': total_terrains,
            'total_coaches': total_coaches,
            'total_reservations': total_reservations,
            'total_revenue': float(total_revenue)
        })
    
    elif request.user.role == 'coach':
        # Coach statistics - skip for now due to schema issues
        try:
            # This would use ReservationCoach when the schema is fixed
            coach_reservations = 0
            total_earnings = 0

            return JsonResponse({
                'total_sessions': coach_reservations,
                'total_earnings': float(total_earnings)
            })
        except Exception as e:
            return JsonResponse({
                'total_sessions': 0,
                'total_earnings': 0
            })
    
    else:
        # Player/Subscriber statistics
        try:
            user_reservations = Reservation.objects.filter(user=request.user).count()
            user_orders = EquipmentOrder.objects.filter(user=request.user).count()
            # Count coach sessions
            user_coach_sessions = ReservationCoach.objects.filter(user=request.user).count()

            return JsonResponse({
                'court_reservations': user_reservations,
                'coach_sessions': user_coach_sessions,
                'equipment_orders': user_orders
            })
        except Exception as e:
            # Fallback if there are database issues
            return JsonResponse({
                'court_reservations': 0,
                'coach_sessions': 0,
                'equipment_orders': 0
            })


# ==================== USER MANAGEMENT ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_list(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admins can view user list'}, status=403)

    users = User.objects.all().values(
        'id', 'username', 'email', 'role', 'date_joined', 'is_active'
    )
    return JsonResponse(list(users), safe=False)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_user_role(request, user_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admins can update user roles'}, status=403)

    user = get_object_or_404(User, id=user_id)
    data = json.loads(request.body)

    user.role = data['role']
    user.save()

    return JsonResponse({'message': 'User role updated successfully'})


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admins can delete users'}, status=403)

    user = get_object_or_404(User, id=user_id)
    if user.role == 'admin':
        return JsonResponse({'error': 'Cannot delete admin users'}, status=400)

    user.delete()
    return JsonResponse({'message': 'User deleted successfully'})


# ==================== NOTIFICATIONS ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    notifications = Notification.objects.filter(user=request.user).values(
        'id', 'title', 'message', 'notification_type', 'is_read', 'created_at'
    )
    return JsonResponse(list(notifications), safe=False)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'message': 'Notification marked as read'})


# ==================== COACH MANAGEMENT ====================

@api_view(['GET'])
def coaches_list(request):
    """Get all coaches with their user information"""
    try:
        coaches = Coach.objects.all().order_by('name')
        coaches_data = []

        for coach in coaches:
            coach_info = {
                'id': coach.id,
                'name': coach.name,
                'email': coach.email,
                'price_per_hour': float(coach.price_per_hour),
                'experience': coach.experience,
                'phone': coach.phone,
                'bio': coach.bio,
                'specialization': coach.specialization,
                'is_active': coach.is_active,
                'created_at': coach.created_at.isoformat() if coach.created_at else None,
                'user_linked': coach.user is not None,
                'user_info': None
            }

            if coach.user:
                coach_info['user_info'] = {
                    'username': coach.user.username,
                    'first_name': coach.user.first_name,
                    'last_name': coach.user.last_name,
                    'role': coach.user.role,
                    'is_active': coach.user.is_active,
                    'date_joined': coach.user.date_joined.isoformat()
                }

            coaches_data.append(coach_info)

        return JsonResponse({
            'coaches': coaches_data,
            'total_coaches': len(coaches_data),
            'linked_coaches': len([c for c in coaches_data if c['user_linked']]),
            'unlinked_coaches': len([c for c in coaches_data if not c['user_linked']])
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== COACH SCHEDULE MANAGEMENT ====================

@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def admin_coach_schedule_management(request):
    """Admin endpoint for managing coach schedules"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    if request.method == 'GET':
        coach_id = request.GET.get('coach_id')
        if coach_id:
            try:
                coach = Coach.objects.get(id=coach_id)
                schedules = Schedule.objects.filter(coach=coach, is_active=True).values(
                    'id', 'day_of_week', 'start_time', 'end_time', 'is_active'
                )
                return JsonResponse({
                    'coach': {
                        'id': coach.id,
                        'name': coach.name,
                        'email': coach.email
                    },
                    'schedules': list(schedules)
                })
            except Coach.DoesNotExist:
                return JsonResponse({'error': 'Coach not found'}, status=404)
        else:
            # Return all coaches with their schedule counts
            coaches = Coach.objects.all()
            coaches_data = []
            for coach in coaches:
                schedule_count = Schedule.objects.filter(coach=coach, is_active=True).count()
                coaches_data.append({
                    'id': coach.id,
                    'name': coach.name,
                    'email': coach.email,
                    'schedule_count': schedule_count
                })
            return JsonResponse({'coaches': coaches_data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            coach_id = data.get('coach_id')
            schedules_data = data.get('schedules', [])

            if not coach_id:
                return JsonResponse({'error': 'Coach ID is required'}, status=400)

            coach = Coach.objects.get(id=coach_id)

            # Clear existing schedules for this coach
            Schedule.objects.filter(coach=coach).update(is_active=False)

            # Create new schedules
            created_schedules = []
            for schedule_data in schedules_data:
                schedule = Schedule.objects.create(
                    coach=coach,
                    day_of_week=schedule_data['day_of_week'],
                    start_time=schedule_data['start_time'],
                    end_time=schedule_data['end_time'],
                    created_by=request.user,
                    is_active=True
                )
                created_schedules.append({
                    'id': schedule.id,
                    'day_of_week': schedule.day_of_week,
                    'start_time': str(schedule.start_time),
                    'end_time': str(schedule.end_time)
                })

            # Generate schedule slots for the next 30 days
            generate_schedule_slots_for_coach(coach)

            return JsonResponse({
                'message': 'Schedule created successfully',
                'schedules': created_schedules
            })

        except Coach.DoesNotExist:
            return JsonResponse({'error': 'Coach not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def coach_schedule(request):
    """Coach endpoint for viewing their own schedule"""
    if request.user.role != 'coach':
        return JsonResponse({'error': 'Coach access required'}, status=403)

    try:
        # First try to get coach by user relationship, then fallback to email
        coach = None
        if hasattr(request.user, 'coach_profile'):
            coach = request.user.coach_profile
        else:
            coach = Coach.objects.get(email=request.user.email)

        # Get weekly schedule
        schedules = Schedule.objects.filter(coach=coach, is_active=True).values(
            'id', 'day_of_week', 'start_time', 'end_time'
        )

        # Get upcoming slots for next 7 days
        from datetime import date, timedelta
        today = date.today()
        upcoming_slots = ScheduleSlot.objects.filter(
            coach=coach,
            date__gte=today,
            date__lte=today + timedelta(days=7)
        ).order_by('date', 'start_time').values(
            'id', 'date', 'start_time', 'end_time', 'is_booked', 'booked_by__username'
        )

        return JsonResponse({
            'weekly_schedule': list(schedules),
            'upcoming_slots': list(upcoming_slots)
        })

    except Coach.DoesNotExist:
        return JsonResponse({'error': 'Coach profile not found'}, status=404)


@api_view(['GET'])
def coach_availability(request, coach_id):
    """Get available slots for a specific coach and date range"""
    try:
        from datetime import datetime, date, timedelta

        coach = Coach.objects.get(id=coach_id)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date:
            start_date = date.today()
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=400)

        if not end_date:
            end_date = start_date + timedelta(days=7)
        else:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=400)

        # Get available slots (not booked)
        available_slots = ScheduleSlot.objects.filter(
            coach=coach,
            date__gte=start_date,
            date__lte=end_date,
            is_booked=False
        ).order_by('date', 'start_time')

        # Format slots data
        slots_data = []
        for slot in available_slots:
            slots_data.append({
                'id': slot.id,
                'date': slot.date.strftime('%Y-%m-%d'),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'is_booked': slot.is_booked
            })

        return JsonResponse({
            'coach': {
                'id': coach.id,
                'name': coach.name,
                'email': coach.email,
                'price_per_hour': float(coach.price_per_hour),
                'specialization': coach.specialization or 'General'
            },
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'available_slots': slots_data,
            'total_available': len(slots_data)
        })

    except Coach.DoesNotExist:
        return JsonResponse({'error': 'Coach not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_schedule(request, schedule_id):
    """Delete a coach schedule (admin only)"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Admin access required'}, status=403)

    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)

        # Check if there are any booked slots for this schedule
        booked_slots = ScheduleSlot.objects.filter(
            created_from_schedule=schedule,
            is_booked=True
        ).count()

        if booked_slots > 0:
            return JsonResponse({
                'error': f'Cannot delete schedule. {booked_slots} slots are already booked.'
            }, status=400)

        # Delete related unbooked slots
        ScheduleSlot.objects.filter(
            created_from_schedule=schedule,
            is_booked=False
        ).delete()

        # Mark schedule as inactive instead of deleting
        schedule.is_active = False
        schedule.save()

        return JsonResponse({'message': 'Schedule deleted successfully'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_schedule_slots_for_coach(coach):
    """Generate schedule slots for a coach based on their weekly schedule"""
    from datetime import date, timedelta
    import calendar

    # Get coach's active schedules
    schedules = Schedule.objects.filter(coach=coach, is_active=True)

    # Generate slots for next 30 days
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    current_date = start_date
    while current_date <= end_date:
        day_name = calendar.day_name[current_date.weekday()].lower()

        # Find schedules for this day
        day_schedules = schedules.filter(day_of_week=day_name)

        for schedule in day_schedules:
            # Check if slot already exists
            existing_slot = ScheduleSlot.objects.filter(
                coach=coach,
                date=current_date,
                start_time=schedule.start_time,
                end_time=schedule.end_time
            ).first()

            if not existing_slot:
                ScheduleSlot.objects.create(
                    coach=coach,
                    date=current_date,
                    start_time=schedule.start_time,
                    end_time=schedule.end_time,
                    created_from_schedule=schedule
                )

        current_date += timedelta(days=1)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def book_coach_slot(request):
    """Book a specific coach slot"""
    try:
        data = json.loads(request.body)
        slot_id = data.get('slot_id')

        if not slot_id:
            return JsonResponse({'error': 'Slot ID is required'}, status=400)

        slot = get_object_or_404(ScheduleSlot, id=slot_id)

        if slot.is_booked:
            return JsonResponse({'error': 'This slot is already booked'}, status=400)

        # Calculate duration and price
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(slot.date, slot.start_time)
        end_datetime = datetime.combine(slot.date, slot.end_time)
        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        total_price = duration_hours * float(slot.coach.price_per_hour)

        # Create reservation
        reservation = ReservationCoach.objects.create(
            user=request.user,
            coach=slot.coach,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            total_price=total_price
        )

        # Mark slot as booked
        slot.is_booked = True
        slot.booked_by = request.user
        slot.save()

        return JsonResponse({
            'message': 'Slot booked successfully',
            'reservation': {
                'id': reservation.id,
                'coach': slot.coach.name,
                'date': str(slot.date),
                'start_time': str(slot.start_time),
                'end_time': str(slot.end_time),
                'total_price': str(total_price)
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def book_coach_session(request):
    """Book a coach session with direct parameters (alternative to slot-based booking)"""
    try:
        data = json.loads(request.body)
        coach_id = data.get('coach_id')
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        # Validate required fields
        if not all([coach_id, date_str, start_time_str, end_time_str]):
            return JsonResponse({'error': 'Coach ID, date, start time, and end time are required'}, status=400)

        # Get coach
        coach = get_object_or_404(Coach, id=coach_id)

        # Parse date and times
        try:
            reservation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time format'}, status=400)

        # Validate date is not in the past
        if reservation_date < timezone.now().date():
            return JsonResponse({'error': 'Cannot book sessions in the past'}, status=400)

        # Validate time range
        if start_time >= end_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

        # Check if coach is available (no existing reservations at this time)
        existing_reservation = ReservationCoach.objects.filter(
            coach=coach,
            date=reservation_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if existing_reservation:
            return JsonResponse({'error': 'Coach is not available at this time'}, status=400)

        # Calculate duration and price
        start_datetime = datetime.combine(reservation_date, start_time)
        end_datetime = datetime.combine(reservation_date, end_time)
        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        total_price = duration_hours * float(coach.price_per_hour)

        # Create reservation
        reservation = ReservationCoach.objects.create(
            user=request.user,
            coach=coach,
            date=reservation_date,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price
        )

        return JsonResponse({
            'message': 'Coach session booked successfully',
            'reservation': {
                'id': reservation.id,
                'coach_name': coach.name,
                'date': reservation_date.strftime('%Y-%m-%d'),
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'total_price': float(total_price),
                'duration_hours': duration_hours
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_coach(request, coach_id):
    """Update coach information"""
    try:
        # Check if user is admin
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)

        coach = get_object_or_404(Coach, id=coach_id)
        data = json.loads(request.body)

        # Update coach fields
        coach.name = data.get('name', coach.name)
        coach.email = data.get('email', coach.email)
        coach.phone = data.get('phone', coach.phone)
        coach.price_per_hour = data.get('price_per_hour', coach.price_per_hour)
        coach.experience = data.get('experience', coach.experience)
        coach.specialization = data.get('specialization', coach.specialization)
        coach.is_active = data.get('is_active', coach.is_active)

        coach.save()

        return JsonResponse({
            'message': 'Coach updated successfully',
            'coach': {
                'id': coach.id,
                'name': coach.name,
                'email': coach.email,
                'phone': coach.phone,
                'price_per_hour': float(coach.price_per_hour),
                'experience': coach.experience,
                'specialization': coach.specialization,
                'is_active': coach.is_active
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_coach_details(request, coach_id):
    """Get detailed coach information for editing"""
    try:
        # Check if user is admin
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)

        coach = get_object_or_404(Coach, id=coach_id)

        return JsonResponse({
            'coach': {
                'id': coach.id,
                'name': coach.name,
                'email': coach.email,
                'phone': coach.phone,
                'price_per_hour': float(coach.price_per_hour),
                'experience': coach.experience,
                'specialization': coach.specialization,
                'is_active': coach.is_active,
                'user_linked': coach.user is not None
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_coach_schedule(request):
    """Create schedule slots for a coach"""
    try:
        # Check if user is admin
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)

        data = json.loads(request.body)
        coach_id = data.get('coach_id')
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if not all([coach_id, date_str, start_time_str, end_time_str]):
            return JsonResponse({'error': 'Coach ID, date, start time, and end time are required'}, status=400)

        coach = get_object_or_404(Coach, id=coach_id)

        # Parse date and times
        try:
            schedule_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time format'}, status=400)

        # Validate time range
        if start_time >= end_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)

        # Check if slot already exists
        existing_slot = ScheduleSlot.objects.filter(
            coach=coach,
            date=schedule_date,
            start_time=start_time,
            end_time=end_time
        ).exists()

        if existing_slot:
            return JsonResponse({'error': 'Schedule slot already exists'}, status=400)

        # Create schedule slot
        schedule_slot = ScheduleSlot.objects.create(
            coach=coach,
            date=schedule_date,
            start_time=start_time,
            end_time=end_time,
            is_booked=False
        )

        return JsonResponse({
            'message': 'Schedule slot created successfully',
            'slot': {
                'id': schedule_slot.id,
                'coach_name': coach.name,
                'date': schedule_slot.date.strftime('%Y-%m-%d'),
                'start_time': schedule_slot.start_time.strftime('%H:%M'),
                'end_time': schedule_slot.end_time.strftime('%H:%M'),
                'is_booked': schedule_slot.is_booked
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_coach_schedule(request, coach_id):
    """Get coach's schedule"""
    try:
        # Check if user is admin
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)

        coach = get_object_or_404(Coach, id=coach_id)

        # Get date range from query params
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                schedule_slots = ScheduleSlot.objects.filter(
                    coach=coach,
                    date__gte=start_date,
                    date__lte=end_date
                ).order_by('date', 'start_time')
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)
        else:
            # Default to next 30 days
            today = timezone.now().date()
            end_date = today + timedelta(days=30)

            schedule_slots = ScheduleSlot.objects.filter(
                coach=coach,
                date__gte=today,
                date__lte=end_date
            ).order_by('date', 'start_time')

        slots_data = []
        for slot in schedule_slots:
            slots_data.append({
                'id': slot.id,
                'date': slot.date.strftime('%Y-%m-%d'),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'is_booked': slot.is_booked
            })

        return JsonResponse({
            'coach_name': coach.name,
            'schedule_slots': slots_data,
            'total_slots': len(slots_data)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_schedule_slot(request, slot_id):
    """Delete a schedule slot"""
    try:
        # Check if user is admin
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)

        slot = get_object_or_404(ScheduleSlot, id=slot_id)

        # Check if slot is booked
        if slot.is_booked:
            return JsonResponse({'error': 'Cannot delete booked schedule slot'}, status=400)

        slot.delete()

        return JsonResponse({'message': 'Schedule slot deleted successfully'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_recent_activities(request):
    """Get recent activities for admin dashboard"""
    try:
        # Check if user is admin
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)

        activities = []

        # Get recent court reservations (last 10)
        try:
            court_reservations = Reservation.objects.select_related('user', 'terrain').order_by('-created_at')[:5]
            for reservation in court_reservations:
                activities.append({
                    'type': 'court_reservation',
                    'icon': 'bi-calendar-check',
                    'color': 'success',
                    'title': 'New Court Reservation',
                    'description': f'{reservation.user.username} booked {reservation.terrain.name}',
                    'details': f'{reservation.date} at {reservation.start_time}',
                    'timestamp': reservation.created_at.isoformat(),
                    'user': reservation.user.username,
                    'relative_time': get_relative_time(reservation.created_at)
                })
        except Exception as e:
            print(f"Error loading court reservations: {e}")

        # Get recent coach reservations (last 10)
        try:
            coach_reservations = CoachReservation.objects.select_related('user', 'coach').order_by('-created_at')[:5]
            for reservation in coach_reservations:
                activities.append({
                    'type': 'coach_reservation',
                    'icon': 'bi-person-check',
                    'color': 'info',
                    'title': 'New Coach Session',
                    'description': f'{reservation.user.username} booked session with {reservation.coach.name}',
                    'details': f'{reservation.date} at {reservation.start_time}',
                    'timestamp': reservation.created_at.isoformat(),
                    'user': reservation.user.username,
                    'relative_time': get_relative_time(reservation.created_at)
                })
        except Exception as e:
            print(f"Error loading coach reservations: {e}")

        # Get recent user registrations (last 5)
        try:
            from core.models import User
            new_users = User.objects.filter(role__in=['joueur', 'abonnée']).order_by('-date_joined')[:3]
            for user in new_users:
                activities.append({
                    'type': 'user_registration',
                    'icon': 'bi-person-plus',
                    'color': 'primary',
                    'title': 'New User Registration',
                    'description': f'{user.username} joined as {user.role}',
                    'details': f'Email: {user.email}',
                    'timestamp': user.date_joined.isoformat(),
                    'user': user.username,
                    'relative_time': get_relative_time(user.date_joined)
                })
        except Exception as e:
            print(f"Error loading new users: {e}")

        # Get recent equipment orders (if any)
        try:
            equipment_orders = EquipmentOrder.objects.select_related('user', 'equipment').order_by('-order_date')[:3]
            for order in equipment_orders:
                activities.append({
                    'type': 'equipment_order',
                    'icon': 'bi-bag-check',
                    'color': 'warning',
                    'title': 'Equipment Order',
                    'description': f'{order.user.username} ordered {order.equipment.name}',
                    'details': f'Quantity: {order.quantity} - Total: ${order.total_price}',
                    'timestamp': order.order_date.isoformat(),
                    'user': order.user.username,
                    'relative_time': get_relative_time(order.order_date)
                })
        except Exception as e:
            print(f"Error loading equipment orders: {e}")

        # Get recent payments
        try:
            payments = Payment.objects.select_related('user').order_by('-payment_date')[:3]
            for payment in payments:
                activities.append({
                    'type': 'payment',
                    'icon': 'bi-credit-card',
                    'color': 'success',
                    'title': 'Payment Received',
                    'description': f'{payment.user.username} made a payment',
                    'details': f'Amount: ${payment.amount} - {payment.payment_method}',
                    'timestamp': payment.payment_date.isoformat(),
                    'user': payment.user.username,
                    'relative_time': get_relative_time(payment.payment_date)
                })
        except Exception as e:
            print(f"Error loading payments: {e}")

        # Sort activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)

        # Return top 15 activities
        return JsonResponse({
            'activities': activities[:15],
            'total_count': len(activities)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_relative_time(timestamp):
    """Get relative time string (e.g., '2 hours ago')"""
    try:
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Recently"


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_coach_reservations(request):
    """Get reservations for the logged-in coach"""
    try:
        # Check if user is a coach
        try:
            coach = Coach.objects.get(user=request.user)
        except Coach.DoesNotExist:
            return JsonResponse({'error': 'User is not a coach'}, status=403)

        # Get all reservations for this coach
        reservations = ReservationCoach.objects.filter(coach=coach).select_related('user').order_by('-date', '-start_time')

        reservations_data = []
        for reservation in reservations:
            reservations_data.append({
                'id': reservation.id,
                'player_name': reservation.user.username,
                'player_email': reservation.user.email,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'total_price': float(reservation.total_price),
                'status': 'confirmed',
                'created_at': reservation.id  # Using ID as proxy for creation order
            })

        # Separate upcoming and past reservations
        from django.utils import timezone
        today = timezone.now().date()

        upcoming_reservations = [r for r in reservations_data if r['date'] >= today.strftime('%Y-%m-%d')]
        past_reservations = [r for r in reservations_data if r['date'] < today.strftime('%Y-%m-%d')]

        return JsonResponse({
            'coach_name': coach.name,
            'total_reservations': len(reservations_data),
            'upcoming_reservations': upcoming_reservations,
            'past_reservations': past_reservations,
            'upcoming_count': len(upcoming_reservations),
            'past_count': len(past_reservations)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_coach_dashboard_stats(request):
    """Get dashboard statistics for the logged-in coach"""
    try:
        # Check if user is a coach
        try:
            coach = Coach.objects.get(user=request.user)
        except Coach.DoesNotExist:
            return JsonResponse({'error': 'User is not a coach'}, status=403)

        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Get all reservations for this coach
        all_reservations = ReservationCoach.objects.filter(coach=coach)

        # Today's reservations
        today_reservations = all_reservations.filter(date=today)

        # This week's reservations
        week_reservations = all_reservations.filter(
            date__gte=start_of_week,
            date__lte=today + timedelta(days=6-today.weekday())
        )

        # This month's reservations
        month_reservations = all_reservations.filter(date__gte=start_of_month)

        # Calculate earnings
        today_earnings = sum([float(r.total_price) for r in today_reservations])
        week_earnings = sum([float(r.total_price) for r in week_reservations])
        month_earnings = sum([float(r.total_price) for r in month_reservations])
        total_earnings = sum([float(r.total_price) for r in all_reservations])

        # Get today's schedule
        today_schedule = ScheduleSlot.objects.filter(coach=coach, date=today).order_by('start_time')

        schedule_data = []
        for slot in today_schedule:
            # Check if this slot is booked
            is_booked = today_reservations.filter(
                start_time=slot.start_time,
                end_time=slot.end_time
            ).exists()

            booking_details = None
            if is_booked:
                reservation = today_reservations.filter(
                    start_time=slot.start_time,
                    end_time=slot.end_time
                ).first()
                if reservation:
                    booking_details = {
                        'player_name': reservation.user.username,
                        'player_email': reservation.user.email,
                        'price': float(reservation.total_price)
                    }

            schedule_data.append({
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'is_booked': is_booked,
                'booking_details': booking_details
            })

        return JsonResponse({
            'coach_info': {
                'name': coach.name,
                'email': coach.email,
                'price_per_hour': float(coach.price_per_hour),
                'specialization': coach.specialization or 'General'
            },
            'stats': {
                'total_reservations': len(all_reservations),
                'today_sessions': len(today_reservations),
                'week_sessions': len(week_reservations),
                'month_sessions': len(month_reservations)
            },
            'earnings': {
                'today': today_earnings,
                'week': week_earnings,
                'month': month_earnings,
                'total': total_earnings
            },
            'today_schedule': schedule_data,
            'schedule_stats': {
                'total_slots': len(schedule_data),
                'booked_slots': len([s for s in schedule_data if s['is_booked']]),
                'available_slots': len([s for s in schedule_data if not s['is_booked']])
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_todays_coach_schedules(request):
    """Get today's schedules for all coaches"""
    try:
        from django.utils import timezone
        from datetime import date

        today = timezone.now().date()

        # Get all coaches
        coaches = Coach.objects.filter(is_active=True)

        coaches_schedules = []

        for coach in coaches:
            # Get today's schedule slots for this coach
            today_slots = ScheduleSlot.objects.filter(
                coach=coach,
                date=today
            ).order_by('start_time')

            # Get coach reservations for today
            coach_reservations = ReservationCoach.objects.filter(
                coach=coach,
                date=today
            ).order_by('start_time')

            # Prepare slots data
            slots_data = []
            for slot in today_slots:
                # Check if this slot is booked
                is_booked = coach_reservations.filter(
                    start_time=slot.start_time,
                    end_time=slot.end_time
                ).exists()

                # Get booking details if booked
                booking_details = None
                if is_booked:
                    reservation = coach_reservations.filter(
                        start_time=slot.start_time,
                        end_time=slot.end_time
                    ).first()
                    if reservation:
                        booking_details = {
                            'player_name': reservation.user.username,
                            'total_price': float(reservation.total_price)
                        }

                slots_data.append({
                    'id': slot.id,
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'is_booked': is_booked,
                    'booking_details': booking_details
                })

            # Calculate stats for this coach
            total_slots = len(slots_data)
            booked_slots = len([slot for slot in slots_data if slot['is_booked']])
            available_slots = total_slots - booked_slots

            # Calculate today's earnings for this coach
            todays_earnings = sum([
                float(reservation.total_price)
                for reservation in coach_reservations
            ])

            coaches_schedules.append({
                'coach': {
                    'id': coach.id,
                    'name': coach.name,
                    'email': coach.email,
                    'price_per_hour': float(coach.price_per_hour),
                    'specialization': coach.specialization or 'General'
                },
                'schedule': {
                    'total_slots': total_slots,
                    'booked_slots': booked_slots,
                    'available_slots': available_slots,
                    'todays_earnings': todays_earnings,
                    'slots': slots_data
                }
            })

        # Calculate overall stats
        total_coaches = len(coaches_schedules)
        total_slots_all = sum([cs['schedule']['total_slots'] for cs in coaches_schedules])
        total_booked_all = sum([cs['schedule']['booked_slots'] for cs in coaches_schedules])
        total_earnings_all = sum([cs['schedule']['todays_earnings'] for cs in coaches_schedules])

        return JsonResponse({
            'date': today.strftime('%Y-%m-%d'),
            'summary': {
                'total_coaches': total_coaches,
                'total_slots': total_slots_all,
                'total_booked': total_booked_all,
                'total_available': total_slots_all - total_booked_all,
                'total_earnings': total_earnings_all
            },
            'coaches_schedules': coaches_schedules
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_weekly_spending(request):
    """Get user's spending for this week"""
    try:
        from django.utils import timezone
        from datetime import timedelta

        # Get start of current week (Monday)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        user = request.user

        # Get court reservations for this week
        court_reservations = Reservation.objects.filter(
            user=user,
            date__gte=start_of_week,
            date__lte=end_of_week
        )

        # Get coach reservations for this week
        coach_reservations = ReservationCoach.objects.filter(
            user=user,
            date__gte=start_of_week,
            date__lte=end_of_week
        )

        # Calculate total spending
        court_spending = sum([float(res.calculate_price()) for res in court_reservations])
        coach_spending = sum([float(res.total_price) for res in coach_reservations if res.total_price])

        total_spending = court_spending + coach_spending

        # Get user's sessions for today
        today_court_sessions = court_reservations.filter(date=today)
        today_coach_sessions = coach_reservations.filter(date=today)

        todays_sessions = []

        # Add court sessions
        for session in today_court_sessions:
            todays_sessions.append({
                'type': 'court',
                'title': f'Court: {session.terrain.name}',
                'time': f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}",
                'price': float(session.calculate_price()),
                'status': 'confirmed'
            })

        # Add coach sessions
        for session in today_coach_sessions:
            todays_sessions.append({
                'type': 'coach',
                'title': f'Coach: {session.coach.name}',
                'time': f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}",
                'price': float(session.total_price) if session.total_price else 0,
                'status': 'confirmed'
            })

        # Sort sessions by time
        todays_sessions.sort(key=lambda x: x['time'])

        return JsonResponse({
            'week_period': {
                'start_date': start_of_week.strftime('%Y-%m-%d'),
                'end_date': end_of_week.strftime('%Y-%m-%d')
            },
            'spending': {
                'court_spending': court_spending,
                'coach_spending': coach_spending,
                'total_spending': total_spending
            },
            'sessions_count': {
                'court_sessions': len(today_court_sessions),
                'coach_sessions': len(today_coach_sessions),
                'total_sessions': len(todays_sessions)
            },
            'todays_sessions': todays_sessions
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== PAYMENT MANAGEMENT ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_payments(request):
    payments = Payment.objects.filter(user=request.user).values(
        'id', 'payment_type', 'amount', 'status', 'payment_date', 'description'
    )
    return JsonResponse(list(payments), safe=False)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_payment(request):
    data = json.loads(request.body)

    payment = Payment.objects.create(
        user=request.user,
        payment_type=data['payment_type'],
        amount=data['amount'],
        description=data['description'],
        transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{request.user.id}"
    )

    return JsonResponse({
        'message': 'Payment created successfully',
        'payment_id': payment.id,
        'transaction_id': payment.transaction_id
    })


# ==================== EQUIPMENT MANAGEMENT (ADMIN) ====================

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_equipment(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admins can add equipment'}, status=403)

    data = json.loads(request.body)
    equipment = Equipment.objects.create(
        name=data['name'],
        type=data['type'],
        brand=data['brand'],
        price=data['price'],
        stock_quantity=data['stock_quantity'],
        description=data.get('description', ''),
        available=data.get('available', True)
    )

    return JsonResponse({
        'message': 'Equipment added successfully',
        'equipment_id': equipment.id
    })


@api_view(['PUT', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def equipment_detail(request, equipment_id):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Only admins can modify equipment'}, status=403)

    equipment = get_object_or_404(Equipment, id=equipment_id)

    if request.method == 'PUT':
        data = json.loads(request.body)
        equipment.name = data.get('name', equipment.name)
        equipment.type = data.get('type', equipment.type)
        equipment.brand = data.get('brand', equipment.brand)
        equipment.price = data.get('price', equipment.price)
        equipment.stock_quantity = data.get('stock_quantity', equipment.stock_quantity)
        equipment.description = data.get('description', equipment.description)
        equipment.available = data.get('available', equipment.available)
        equipment.save()
        return JsonResponse({'message': 'Equipment updated successfully'})

    elif request.method == 'DELETE':
        equipment.delete()
        return JsonResponse({'message': 'Equipment deleted successfully'})


# ==================== SUBSCRIPTION MANAGEMENT ====================

@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_subscriptions(request):
    """Get user's subscriptions or create a new subscription"""
    if request.method == 'GET':
        try:
            # Get user's current subscription
            subscription = Subscription.objects.filter(user=request.user).first()

            if subscription:
                subscription_data = {
                    'id': subscription.id,
                    'plan_type': subscription.plan_type,
                    'start_date': subscription.start_date.strftime('%Y-%m-%d'),
                    'end_date': subscription.end_date.strftime('%Y-%m-%d'),
                    'status': subscription.status,
                    'monthly_price': float(subscription.monthly_price),
                    'auto_renew': subscription.auto_renew,
                    'is_active': subscription.is_active,
                    'days_remaining': (subscription.end_date.date() - timezone.now().date()).days if subscription.is_active else 0
                }
                return JsonResponse({'subscription': subscription_data})
            else:
                return JsonResponse({'subscription': None, 'message': 'No active subscription'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_type = data.get('plan_type')
            duration_months = data.get('duration_months', 1)

            # Validate input
            if not plan_type:
                return JsonResponse({'error': 'Plan type is required'}, status=400)

            # Calculate price based on plan type
            price_map = {
                'basic': 29.99,
                'premium': 49.99,
                'vip': 79.99
            }

            monthly_price = price_map.get(plan_type, 29.99)

            # Check if user already has a subscription (OneToOneField)
            existing_subscription = Subscription.objects.filter(user=request.user).first()

            if existing_subscription:
                if existing_subscription.is_active:
                    return JsonResponse({'error': 'You already have an active subscription'}, status=400)
                else:
                    # Update existing subscription instead of creating new one
                    from datetime import timedelta
                    existing_subscription.plan_type = plan_type
                    existing_subscription.end_date = timezone.now() + timedelta(days=30 * duration_months)
                    existing_subscription.monthly_price = monthly_price
                    existing_subscription.status = 'active'
                    existing_subscription.auto_renew = True
                    existing_subscription.save()

                    # Create payment record
                    Payment.objects.create(
                        user=request.user,
                        payment_type='subscription',
                        amount=monthly_price * duration_months,
                        status='completed',
                        transaction_id=f'SUB_{existing_subscription.id}_{int(timezone.now().timestamp())}',
                        description=f'{plan_type.title()} subscription for {duration_months} month(s)'
                    )

                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        title='Subscription Reactivated',
                        message=f'Your {plan_type.title()} subscription has been reactivated successfully!',
                        notification_type='subscription'
                    )

                    return JsonResponse({
                        'message': 'Subscription reactivated successfully',
                        'subscription_id': existing_subscription.id
                    })

            # Calculate end date for new subscription
            from datetime import timedelta
            end_date = timezone.now() + timedelta(days=30 * duration_months)

            # Create new subscription (start_date is auto_now_add)
            subscription = Subscription.objects.create(
                user=request.user,
                plan_type=plan_type,
                end_date=end_date,
                monthly_price=monthly_price,
                status='active'
            )

            # Create payment record
            Payment.objects.create(
                user=request.user,
                payment_type='subscription',
                amount=monthly_price * duration_months,
                status='completed',
                transaction_id=f'SUB_{subscription.id}_{int(timezone.now().timestamp())}',
                description=f'{plan_type.title()} subscription for {duration_months} month(s)'
            )

            # Create notification
            Notification.objects.create(
                user=request.user,
                title='Subscription Activated',
                message=f'Your {plan_type.title()} subscription has been activated successfully!',
                notification_type='subscription'
            )

            return JsonResponse({
                'message': 'Subscription created successfully',
                'subscription_id': subscription.id
            })

        except Exception as e:
            import traceback
            from django.db import IntegrityError

            # Handle specific database constraint errors
            if 'UNIQUE constraint failed' in str(e) or isinstance(e, IntegrityError):
                return JsonResponse({'error': 'You already have a subscription. Please cancel your current subscription before creating a new one.'}, status=400)

            print(f"Subscription creation error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': f'Subscription creation failed: {str(e)}'}, status=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """Cancel user's subscription"""
    try:
        subscription = Subscription.objects.filter(
            user=request.user,
            status='active'
        ).first()

        if not subscription:
            return JsonResponse({'error': 'No active subscription found'}, status=404)

        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.save()

        # Create notification
        Notification.objects.create(
            user=request.user,
            title='Subscription Cancelled',
            message='Your subscription has been cancelled. You can continue using premium features until the end of your billing period.',
            notification_type='subscription'
        )

        return JsonResponse({'message': 'Subscription cancelled successfully'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def subscription_plans(request):
    """Get available subscription plans"""
    try:
        plans = [
            {
                'type': 'basic',
                'name': 'Basic Plan',
                'price': 29.99,
                'features': [
                    '🏟️ Court reservations',
                    '🎾 Basic equipment access',
                    '📧 Email support',
                    '⏰ 2 court hours per month'
                ],
                'popular': False
            },
            {
                'type': 'premium',
                'name': 'Premium Plan',
                'price': 49.99,
                'features': [
                    '🏟️ Unlimited court reservations',
                    '👨‍🏫 Coach session discounts',
                    '🎾 Premium equipment access',
                    '⭐ Priority booking',
                    '🏆 Tournament entry discounts',
                    '📞 Phone support'
                ],
                'popular': True
            },
            {
                'type': 'vip',
                'name': 'VIP Plan',
                'price': 79.99,
                'features': [
                    '✨ All Premium features',
                    '👨‍🏫 Free coach sessions (2 per month)',
                    '🏟️ Exclusive VIP courts',
                    '🎾 Personal equipment storage',
                    '🏆 Free tournament entries',
                    '🌟 24/7 concierge support',
                    '👥 Guest passes (4 per month)'
                ],
                'popular': False
            }
        ]

        return JsonResponse({'plans': plans})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== PLAYER RESERVATIONS ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def player_reservations(request):
    """Get player's own reservations (both court and coach)"""
    try:
        # Get court reservations
        court_reservations = Reservation.objects.filter(user=request.user).order_by('-date', '-start_time')

        court_data = []
        for reservation in court_reservations:
            court_data.append({
                'id': reservation.id,
                'type': 'court',
                'court_name': reservation.terrain.name,
                'location': reservation.terrain.location,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'price': float(reservation.calculate_price()),
                'status': 'upcoming' if reservation.date >= timezone.now().date() else 'completed'
            })

        # Get coach reservations
        coach_reservations = ReservationCoach.objects.filter(user=request.user).order_by('-date', '-start_time')

        coach_data = []
        for reservation in coach_reservations:
            coach_data.append({
                'id': reservation.id,
                'type': 'coach',
                'coach_name': reservation.coach.name,
                'coach_email': reservation.coach.email,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'price': float(reservation.total_price),
                'status': 'upcoming' if reservation.date >= timezone.now().date() else 'completed'
            })

        # Combine and sort all reservations by date
        all_reservations = court_data + coach_data
        all_reservations.sort(key=lambda x: (x['date'], x['start_time']), reverse=True)

        # Separate upcoming and past reservations
        upcoming_reservations = [r for r in all_reservations if r['status'] == 'upcoming']
        past_reservations = [r for r in all_reservations if r['status'] == 'completed']

        return JsonResponse({
            'upcoming_reservations': upcoming_reservations,
            'past_reservations': past_reservations,
            'total_reservations': len(all_reservations),
            'upcoming_count': len(upcoming_reservations),
            'past_count': len(past_reservations)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def player_upcoming_reservations(request):
    """Get player's upcoming reservations only"""
    try:
        from datetime import date
        today = date.today()

        # Get upcoming court reservations
        upcoming_court = Reservation.objects.filter(
            user=request.user,
            date__gte=today
        ).order_by('date', 'start_time')

        court_data = []
        for reservation in upcoming_court:
            court_data.append({
                'id': reservation.id,
                'type': 'court',
                'title': f"Court: {reservation.terrain.name}",
                'court_name': reservation.terrain.name,
                'location': reservation.terrain.location,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'price': float(reservation.calculate_price()),
                'icon': '🏟️'
            })

        # Get upcoming coach reservations
        upcoming_coach = ReservationCoach.objects.filter(
            user=request.user,
            date__gte=today
        ).order_by('date', 'start_time')

        coach_data = []
        for reservation in upcoming_coach:
            coach_data.append({
                'id': reservation.id,
                'type': 'coach',
                'title': f"Coach: {reservation.coach.name}",
                'coach_name': reservation.coach.name,
                'coach_email': reservation.coach.email,
                'date': reservation.date.strftime('%Y-%m-%d'),
                'start_time': reservation.start_time.strftime('%H:%M'),
                'end_time': reservation.end_time.strftime('%H:%M'),
                'price': float(reservation.total_price),
                'icon': '🎾'
            })

        # Combine and sort by date/time
        upcoming_reservations = court_data + coach_data
        upcoming_reservations.sort(key=lambda x: (x['date'], x['start_time']))

        return JsonResponse({
            'upcoming_reservations': upcoming_reservations,
            'count': len(upcoming_reservations)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
