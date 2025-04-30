from django.db import models
from cloudinary.models import CloudinaryField

class Event(models.Model):
    EVENT_TYPES = (
        ('Conference', 'Conference'),
        ('Workshop', 'Workshop'),
        ('Hackathon', 'Hackathon'),
        ('Meetup', 'Meetup'),
        ('Webinar', 'Webinar'),
        ('Other', 'Other'),
    )
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.CharField(max_length=50)
    time = models.CharField(max_length=50)
    location = models.CharField(max_length=200)
    is_online = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=EVENT_TYPES)
    tags = models.JSONField()
    organizer = models.CharField(max_length=100)
    organizer_image = models.CharField(max_length=200, blank=True, null=True)
    attendees = models.IntegerField(default=0)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    spots_left = models.IntegerField(default=0)
    # Add user relationship - the creator of the event
    created_by = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['date']


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image')

    def __str__(self):
        return self.event.title
