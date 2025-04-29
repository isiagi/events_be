from django.contrib import admin
from .models import Event

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'type', 'attendees', 'spots_left')
    list_filter = ('is_online', 'type', 'is_free')
    search_fields = ('title', 'description', 'organizer')

admin.site.register(Event, EventAdmin)
