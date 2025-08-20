from django.urls import path
from . import views

urlpatterns = [
    # List (GET) + Create (POST)
    path("", views.events_view, name="events-list-create"),

    # Retrieve (GET) + Update (PUT) + Delete (DELETE)
    path("<str:event_id>/", views.event_detail_view, name="event-detail"),

    # Attend an event (POST)
    path("<str:event_id>/attend/", views.attend_event_view, name="event-attend"),

    # Unattend an event (POST)
    path("<str:event_id>/unattend/", views.unattend_event_view, name="event-unattend"),
]
