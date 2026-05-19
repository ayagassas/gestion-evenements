from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.home, name='home'),

    # Public event pages
    path('events/<int:pk>/', views.event_detail, name='detail'),
    path('events/<int:pk>/register/', views.register_for_event, name='register'),
    path('events/<int:pk>/unregister/', views.unregister_from_event, name='unregister'),
    path('tickets/<int:registration_id>/download/', views.download_ticket, name='download_ticket'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),

    # Organizer
    path('organizer/', views.organizer_dashboard, name='organizer_dashboard'),
    path('organizer/events/new/', views.event_create, name='event_create'),
    path('organizer/events/<int:pk>/edit/', views.event_update, name='event_update'),
    path('organizer/events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:pk>/participants/', views.event_participants, name='participants'),
    path('registrations/<int:registration_id>/checkin/', views.check_in, name='check_in'),
    path('organizer/stats/', views.stats_dashboard, name='stats'),

    # Admin
    path('manage/users/', views.admin_users, name='admin_users'),
    path('manage/users/<int:user_id>/role/', views.admin_user_set_role, name='admin_user_set_role'),
    path('manage/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('manage/events/', views.admin_events, name='admin_events'),
    path('manage/events/<int:pk>/delete/', views.admin_event_delete, name='admin_event_delete'),
]
