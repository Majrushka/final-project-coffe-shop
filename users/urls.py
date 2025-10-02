from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    # Страница регистрации
    path('register/', views.register, name='register'),
]