from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User

class Group(models.Model):
    CATEGORY_CHOICES = [
        ('TECH', 'Technology'),
        ('HEALTH', 'Health & Wellness'),
        ('EDUCATION', 'Education'),
        ('SOCIAL', 'Social'),
        ('HOBBY', 'Hobbies & Interests'),
        ('PROFESSIONAL', 'Professional'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.URLField()
    cover_image = models.URLField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = ArrayField(models.CharField(max_length=50), blank=True)
    location = models.CharField(max_length=255)
    is_online = models.BooleanField(default=False)
    member_count = models.PositiveIntegerField(default=1)
    event_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='group')
    
    def __str__(self):
        return self.name