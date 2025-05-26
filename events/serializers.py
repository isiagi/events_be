from rest_framework import serializers
from .models import Event, EventImage, EventRegistration
from django.conf import settings
import json


class EventImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = EventImage
        fields = '__all__'

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                # Ensure we're using the full URL including scheme and domain
                return request.build_absolute_uri(obj.image.url)
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

class EventSerializer(serializers.ModelSerializer):

    images = EventImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False)
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'date', 'time','registration_url', 'organizer','organizer_image', 'location', 'is_online', 'type', 'tags', 'organizer', 'attendees', 'is_free', 'price', 'spots_left', 'images', 'uploaded_images', 'created_by', 'groupId', 'slug']

    
    def validate_tags(self, value):
        # Ensure tags is always a list
        if isinstance(value, str):
            return [tag.strip() for tag in value.split(',') if tag.strip()]
        return value
    


class EventCreateSerializer(serializers.ModelSerializer):

    images = EventImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    
   
    class Meta:
        model = Event
        fields = '__all__'

    def validate_tags(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
                else:
                    raise serializers.ValidationError("Tags must be a list.")
            except json.JSONDecodeError:
                raise serializers.ValidationError("Value must be valid hhhj JSON.")
        raise serializers.ValidationError("Invalid format for tags.")
        

    
    def create(self, validated_data):
        print(validated_data, 'validated_data')
        images_data = validated_data.pop('uploaded_images', [])
        event = Event.objects.create(**validated_data)
        for image_data in images_data:
            EventImage.objects.create(event=event, image=image_data)
        return event
    


class EventRegistrationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(read_only=True)
    user_email = serializers.EmailField(read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = ['id', 'event', 'user_id', 'user_name', 'user_email', 'registered_at']
        read_only_fields = ['registered_at']

class EventWithRegistrationSerializer(EventSerializer):
    """
    Event serializer that includes registration status for the current user
    """
    is_registered = serializers.SerializerMethodField()
    
    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return EventRegistration.objects.filter(
                event=obj, 
                user_id=request.user.id
            ).exists()
        return False
    
    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ['is_registered']