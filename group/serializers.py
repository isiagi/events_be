# serializers.py
from rest_framework import serializers
from .models import Group, GroupImage
from django.contrib.auth.models import User
from django.conf import settings
from events.serializers import EventSerializer

class UserSerializer(serializers.ModelSerializer):
    clerk_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'clerk_id']
    
    def get_clerk_id(self, obj):
        # The username is the Clerk ID in your authentication system
        return obj.username

class GroupImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupImage
        fields = ['id', 'image', 'is_cover', 'created_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                # Ensure we're using the full URL including scheme and domain
                return request.build_absolute_uri(obj.image.url)
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

class GroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    images = GroupImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    uploaded_cover_image = serializers.ImageField(
        max_length=1000000, 
        allow_empty_file=False, 
        use_url=False,
        write_only=True,
        required=False
    )
    cover_image_url = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    member_count = serializers.ReadOnlyField()
    event_count = serializers.ReadOnlyField()

    events = EventSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'tags', 
            'location', 'is_online', 'member_count', 'event_count',
            'created_at', 'owner', 'members', 'images', 'uploaded_images', 
            'uploaded_cover_image', 'cover_image_url', 'primary_image_url',
            'events'
        ]
        read_only_fields = [
            'slug', 'created_at', 'member_count', 'event_count', 
            'owner', 'members'
        ]
    
    def get_cover_image_url(self, obj):
        cover_image = obj.images.filter(is_cover=True).first()
        if cover_image and cover_image.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(cover_image.image.url)
            return cover_image.image.url
        return None
    
    def get_primary_image_url(self, obj):
        primary_image = obj.images.filter(is_cover=False).first()
        if primary_image and primary_image.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None
    
    def create(self, validated_data):
        # Get the current user from the request
        user = self.context['request'].user
        
        # Extract image data
        regular_images = validated_data.pop('uploaded_images', [])
        cover_image = validated_data.pop('uploaded_cover_image', None)
        
        # Create the group with that user as owner
        group = Group.objects.create(
            owner=user,
            member_count=1,
            event_count=0,
            **validated_data
        )
        
        # Add the creator as the first member
        group.members.add(user)
        
        # Save the cover image if provided
        if cover_image:
            GroupImage.objects.create(
                group=group,
                image=cover_image,
                is_cover=True
            )
        
        # Save regular images
        for image_data in regular_images:
            GroupImage.objects.create(
                group=group,
                image=image_data,
                is_cover=False
            )
        
        return group
    
    def update(self, instance, validated_data):
        # Extract image data
        regular_images = validated_data.pop('uploaded_images', [])
        cover_image = validated_data.pop('uploaded_cover_image', None)
        
        # Update the group instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create cover image
        if cover_image:
            # Delete existing cover images
            GroupImage.objects.filter(group=instance, is_cover=True).delete()
            # Create new cover image
            GroupImage.objects.create(
                group=instance,
                image=cover_image,
                is_cover=True
            )
        
        # Add new regular images
        for image_data in regular_images:
            GroupImage.objects.create(
                group=instance,
                image=image_data,
                is_cover=False
            )
        
        return instance

# Legacy serializer for backward compatibility if needed
class LegacyGroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'image', 'cover_image', 'category', 
                 'tags', 'location', 'is_online', 'member_count', 'event_count', 
                 'created_at', 'owner', 'members']
        read_only_fields = ['created_at', 'member_count', 'event_count', 'owner', 'members']
    
    def get_image(self, obj):
        return obj.primary_image_url
    
    def get_cover_image(self, obj):
        return obj.cover_image_url