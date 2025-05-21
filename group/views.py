from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Group
from .serializers import GroupSerializer
# from authentication import ClerkAuthentication  # Import your custom authentication

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
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
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