from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
import logging

logger = logging.getLogger(__name__)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Added JSONParser for flexibility
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_online', 'is_free']
    search_fields = ['title', 'description', 'location', 'organizer']
    ordering_fields = ['date', 'price', 'attendees']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Override create method to add better error handling and debugging
        """
        # Debug logging
        logger.debug(f"Create event request data: {request.data}")
        logger.debug(f"Create event request FILES: {request.FILES}")
        
        # Handle tags pre-processing if needed
        mutable_data = request.data.copy()
        
        # Check if tags needs preprocessing
        if 'tags' in mutable_data:
            try:
                tags_data = mutable_data['tags']
                logger.debug(f"Raw tags data: {tags_data}")
                
                # If it's a string that looks like JSON but isn't parsed yet
                if isinstance(tags_data, str) and tags_data.startswith('['):
                    try:
                        # Parse JSON string to verify it's valid
                        parsed_tags = json.loads(tags_data)
                        logger.debug(f"Parsed tags: {parsed_tags}")
                        # Keep it as is, serializer will handle it
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON for tags: {e}")
                        # If JSON is invalid, default to basic tag
                        mutable_data['tags'] = json.dumps(['uncategorized'])
            except Exception as e:
                logger.error(f"Error processing tags: {e}")
                mutable_data['tags'] = json.dumps(['uncategorized'])
        
        # Create serializer with possibly modified data
        serializer = self.get_serializer(data=mutable_data)
        
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        # Enhanced error response with details
        logger.error(f"Serializer validation errors: {serializer.errors}")
        return Response({
            'error': 'Invalid data provided',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Custom endpoint to get upcoming events sorted by date"""
        # In a real app, you would filter by date > today
        events = self.get_queryset().order_by('date')[:10]
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Custom endpoint to register for an event"""
        event = self.get_object()
        if event.spots_left > 0:
            event.attendees += 1
            event.spots_left -= 1
            event.save()
            return Response({'status': 'registered'})
        return Response({'status': 'no spots left'}, status=status.HTTP_400_BAD_REQUEST)