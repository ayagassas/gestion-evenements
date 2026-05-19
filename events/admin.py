from django.contrib import admin
from .models import Event, Notification, Registration, Ticket


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'organizer', 'created_at')
    list_filter = ('date',)
    search_fields = ('title', 'description', 'location')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'checked_in', 'created_at')
    list_filter = ('status', 'checked_in')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'registration', 'created_at')
    search_fields = ('code',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'read', 'created_at')
    list_filter = ('read',)
