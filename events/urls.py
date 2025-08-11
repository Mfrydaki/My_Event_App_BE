from django.urls import path
from . import views

urlpatterns = [
    # List + Create
    path('events/', views.events_view, name='events-list-create'),

    # Retrieve + Update + Delete
    path('events/<str:event_id>/', views.event_detail_view, name='event-detail'),
]
