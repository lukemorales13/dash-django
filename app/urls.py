from django.contrib import admin
from django.urls import path, include
from .views import main_dashboard

urlpatterns = [
    path('main/', main_dashboard, name='main_dashboard'),
]