from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Group
from .serializers import GroupSerializer
# from authentication import ClerkAuthentication  # Import your custom authentication
from django.http import Http404
from django.utils.text import slugify

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.owner == request.user

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # authentication_classes = [ClerkAuthentication]
    # permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'slug'

    # def get_permissions(self):
    #     """
    #     Instantiates and returns the list of permissions that this view requires.
    #     """
    #     if self.action in ['list', 'retrieve']:
    #         # Allow unauthenticated access for listing groups and retrieving individual groups
    #         permission_classes = [permissions.AllowAny]
    #     else:
    #         # For all other actions (create, update, delete, join, leave), use default permissions
    #         permission_classes = self.permission_classes
        
    #     return [permission() for permission in permission_classes]

    def get_object(self):
        """
        Override to handle slug lookups with spaces and special characters
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        
        # Get the slug from URL
        slug_from_url = self.kwargs.get(lookup_url_kwarg)
        
        # Try direct lookup first (exact match)
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.filter(slug=slug_from_url).first()
        
        # If not found, always try with normalized slug
        if not obj:
            normalized_slug = slugify(slug_from_url)
            obj = queryset.filter(slug=normalized_slug).first()
        
        if obj is None:
            raise Http404(f"No event found with slug: {slug_from_url}")
            
        return obj
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        group = self.get_object()
        user = request.user
        
        if user in group.members.all():
            return Response({'detail': 'User is already a member of this group.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        group.members.add(user)
        group.member_count = group.members.count()
        group.save()
        
        return Response({'detail': 'Successfully joined the group.'}, 
                       status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        group = self.get_object()
        user = request.user
        
        if user not in group.members.all():
            return Response({'detail': 'User is not a member of this group.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        if user == group.owner:
            return Response({'detail': 'Owner cannot leave the group. Transfer ownership first.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        group.members.remove(user)
        group.member_count = group.members.count()
        group.save()
        
        return Response({'detail': 'Successfully left the group.'}, 
                       status=status.HTTP_200_OK)