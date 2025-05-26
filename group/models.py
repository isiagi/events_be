# models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.utils.text import slugify

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
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    description = models.TextField()
    # Replace URLFields with relationship to GroupImage model
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = ArrayField(models.CharField(max_length=50), blank=True)
    location = models.CharField(max_length=255)
    is_online = models.BooleanField(default=False)
    member_count = models.PositiveIntegerField(default=1)
    event_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='group')
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def primary_image(self):
        """Return the first uploaded image as the group's primary image"""
        main_image = self.images.filter(is_cover=False).first()
        return main_image.image if main_image else None
    
    @property
    def cover_image(self):
        """Return the group's cover image"""
        cover = self.images.filter(is_cover=True).first()
        return cover.image if cover else None
    
    class Meta:
        ordering = ['-created_at']


class GroupImage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image', folder='groups')
    is_cover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_cover', '-created_at']
    
    def __str__(self):
        image_type = "Cover" if self.is_cover else "Profile"
        return f"{image_type} image for {self.group.name}"