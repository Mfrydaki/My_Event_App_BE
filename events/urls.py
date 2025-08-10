from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.event_list, name='event_list'), #event list
    path('test/', views.test_api) #test endpoint
]
