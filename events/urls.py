from django.urls import path
from . import views
urlpatterns = [
    # List + Create
        path('events/', views.events_view, name='events-list-create'),

    # Retrieve + Update + Delete
    path('events/<str:event_id>/', views.event_detail_view, name='event-detail'),

    # Attend an event
    path('events/<str:event_id>/attend/', views.attend_event_view, name='event-attend'),

    # Unattend an event
    path('events/<str:event_id>/unattend/', views.unattend_event_view, name='event-unattend'),
]
 