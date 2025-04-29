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