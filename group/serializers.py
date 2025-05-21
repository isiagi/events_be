from rest_framework import serializers
from .models import Group
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    clerk_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'clerk_id']
    
    def get_clerk_id(self, obj):
        # The username is the Clerk ID in your authentication system
        return obj.username

class GroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'image', 'cover_image', 'category', 
                 'tags', 'location', 'is_online', 'member_count', 'event_count', 
                 'created_at', 'owner', 'members']
        read_only_fields = ['created_at', 'member_count', 'event_count', 'owner', 'members']
    
    def create(self, validated_data):
        # Get the current user from the request
        user = self.context['request'].user
        
        # Create the group with that user as owner
        group = Group.objects.create(
            owner=user,
            member_count=1,
            event_count=0,
            **validated_data
        )
        
        # Add the creator as the first member
        group.members.add(user)
        
        return group