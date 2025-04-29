from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Event

class EventTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.event_data = {
            'title': 'TechConnect Hackathon 2023',
            'description': 'Join us for a 48-hour coding challenge!',
            'date': 'Oct 15-17, 2023',
            'time': '9:00 AM - 5:00 PM',
            'location': 'San Francisco, CA',
            'is_online': False,
            'type': 'Hackathon',
            'tags': ['coding', 'innovation', 'technology'],
            'image': '/images/hackathon.jpg',
            'organizer': 'TechConnect',
            'organizer_image': '/images/organizer1.jpg',
            'attendees': 120,
            'is_free': False,
            'price': 25.00,
            'spots_left': 30,
        }
        self.event = Event.objects.create(**self.event_data)
    
    def test_get_all_events(self):
        response = self.client.get(reverse('event-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_create_event(self):
        new_event = self.event_data.copy()
        new_event['title'] = 'New Hackathon 2023'
        response = self.client.post(
            reverse('event-list'), 
            new_event, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
