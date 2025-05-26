from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventRegistration
from .serializers import EventSerializer, EventCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
import logging
from django.utils.text import slugify
from django.http import Http404
from django.db import transaction

logger = logging.getLogger(__name__)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_online', 'is_free']
    search_fields = ['title', 'description', 'location', 'organizer']
    ordering_fields = ['date', 'price', 'attendees']
    lookup_field = 'slug'

    def get_object(self):
        """
        Override to handle slug lookups with spaces and special characters
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        
        # Get the slug from URL
        slug_from_url = self.kwargs.get(lookup_url_kwarg)
        
        # Try direct lookup first (exact match)
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.filter(slug=slug_from_url).first()
        
        # If not found, always try with normalized slug
        if not obj:
            normalized_slug = slugify(slug_from_url)
            obj = queryset.filter(slug=normalized_slug).first()
        
        if obj is None:
            raise Http404(f"No event found with slug: {slug_from_url}")
            
        return obj

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer    

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Custom endpoint to get upcoming events sorted by date"""
        events = self.get_queryset().order_by('date')[:10]
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def register(self, request, slug=None):
        """Custom endpoint to register for an event"""
        event = self.get_object()
        
        # Get user info from Clerk token (you should have middleware that sets this)
        user_id = request.user.id  # This should be the Clerk user ID
        # user_email = getattr(request.user, 'email', None)
        # user_name = getattr(request.user, 'first_name', '') + ' ' + getattr(request.user, 'last_name', '')
        # user_name = user_name.strip() or getattr(request.user, 'username', None)

        # print(request.data, 'request data')
        # user_email = request.data.get('email')
        # user_name = request.data.get('name')
        user_email = request.user.email
        user_name = request.user.first_name + ' ' + request.user.last_name

        print(f"Request user: {request.user.email}")

        print(f"User ID: {user_id}")
        print(f"User Email: {user_email}")
        print(f"User Name: {user_name}")

        # Check if the event uses external registration
        if event.registration_url:
            return Response({
                'status': 'external_registration',
                'registration_url': event.registration_url
            })
        
        # Check if user is already registered
        if EventRegistration.objects.filter(event=event, user_id=user_id).exists():
            return Response({
                'status': 'already_registered',
                'message': 'You are already registered for this event'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if spots are available
        if event.spots_left <= 0:
            return Response({
                'status': 'no_spots_left',
                'message': 'This event is fully booked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Register user for the event using a database transaction
        with transaction.atomic():
            # Create registration record
            EventRegistration.objects.create(
                event=event,
                user_id=user_id,
                user_email=request.user.email,
                user_name=user_name
            )
            
            # Update event counts
            event.attendees += 1
            event.spots_left -= 1
            event.save(update_fields=['attendees', 'spots_left'])
        
        return Response({
            'status': 'registered',
            'message': 'Successfully registered for the event'
        })
    
    @action(detail=True, methods=['post'])
    def unregister(self, request, slug=None):
        """Custom endpoint to unregister from an event"""
        event = self.get_object()
        user_id = request.user.id

        print(f"Request user: {request.user.email}")
        
        try:
            # Use transaction to ensure data consistency
            with transaction.atomic():
                registration = EventRegistration.objects.get(event=event, user_id=user_id)
                registration.delete()
                
                # Update event counts
                event.attendees -= 1
                event.spots_left += 1
                event.save(update_fields=['attendees', 'spots_left'])
            
            return Response({
                'status': 'unregistered',
                'message': 'Successfully unregistered from the event'
            })
        except EventRegistration.DoesNotExist:
            return Response({
                'status': 'not_registered',
                'message': 'You are not registered for this event'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """
        Custom endpoint to get all events created by the current user
        """
        user_id = request.user
        events = self.get_queryset().filter(created_by=user_id)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
        """
        Custom endpoint to get all events the current user is registered for
        """
        user_id = request.user.id
        
        # Get registrations for this user
        registrations = EventRegistration.objects.filter(user_id=user_id).select_related('event')
        event_ids = [reg.event.id for reg in registrations]
        
        # Get the events
        events = self.get_queryset().filter(id__in=event_ids)
        serializer = self.get_serializer(events, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attendees(self, request, slug=None):
        """
        Custom endpoint to get all attendees for an event
        Only accessible by event creator
        """
        event = self.get_object()
        user_id = request.user
        
        # Check if user is the event creator (optional security check)
        if str(event.created_by) != str(user_id):
            return Response({
                'error': 'You can only view attendees for events you created'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all registrations for this event
        registrations = EventRegistration.objects.filter(event=event).order_by('-registered_at')
        
        attendees_data = []
        for registration in registrations:
            attendees_data.append({
                'user_id': registration.user_id,
                'user_name': registration.user_name,
                'user_email': registration.user_email,
                'registered_at': registration.registered_at
            })
        
        return Response({
            'event': event.title,
            'total_attendees': len(attendees_data),
            'attendees': attendees_data
        })