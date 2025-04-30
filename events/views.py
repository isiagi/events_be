from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
import logging
from django.utils.text import slugify

logger = logging.getLogger(__name__)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Added JSONParser for flexibility
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
        
        # If not found and slug contains spaces, try with a normalized version
        if not obj and ' ' in slug_from_url:
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
        # In a real app, you would filter by date > today
        events = self.get_queryset().order_by('date')[:10]
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def register(self, request, slug=None):
        """Custom endpoint to register for an event"""
        event = self.get_object()
        if event.spots_left > 0:
            event.attendees += 1
            event.spots_left -= 1
            event.save()
            return Response({'status': 'registered'})
        return Response({'status': 'no spots left'}, status=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """
        Custom endpoint to get all events created by the current user
        URL: /api/events/my_events/
        """
        # Get the user from the request
        user = request.user

        # Filter events where created_by matches the current user
        events = self.get_queryset().filter(created_by=user)

        
        # Serialize the filtered events
        serializer = self.get_serializer(events, many=True)

        
        return Response(serializer.data)