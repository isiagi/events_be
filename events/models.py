from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from django.utils import timezone

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
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
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
    registration_url = models.URLField(blank=True, null=True)
    groupId = models.ForeignKey('group.Group', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Make sure spots_left is calculated correctly
        # if not self.id:  # New event
        #     self.spots_left = self.capacity - self.attendees
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['date']


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image')

    def __str__(self):
        return self.event.title
    


class EventRegistration(models.Model):
    """
    Model to track user registrations for events
    """
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='registrations')
    user_id = models.CharField(max_length=200)  # Clerk user ID
    user_email = models.EmailField(blank=True, null=True)  # Store user email for easy reference
    user_name = models.CharField(max_length=200, blank=True, null=True)  # Store user name
    registered_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['event', 'user_id']  # Prevent duplicate registrations
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.user_name or self.user_id} - {self.event.title}"
