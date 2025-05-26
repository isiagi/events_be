from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Group
from .serializers import GroupSerializer
from django.http import Http404
from django.utils.text import slugify
from authentication.auth import ClerkAuthentication



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def debug_auth(request):
    print("User:", request.user)
    print("Auth:", request.auth_token)
    return Response({
        "user": str(request.user),
        "auth": str(request.auth_token)
    })

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = 'slug'
 



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
            raise Http404(f"No group found with slug: {slug_from_url}")
            
        return obj
    

    # Get groups created by the current user
    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        groups = self.get_queryset().filter(owner=request.user.id)
        serializer = self.get_serializer(groups, many=True)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['post'])
    def join(self, request, slug=None):
        group = self.get_object()
        user = request.user

        print(f"Request user: {request.user.email}")
        
        if user in group.members.all():
            return Response({'detail': 'User is already a member of this group.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        group.members.add(user)
        group.member_count = group.members.count()
        group.save()
        
        return Response({'detail': 'Successfully joined the group.'}, 
                       status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, slug=None):
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