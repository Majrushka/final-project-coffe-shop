
from django.urls import path
from .views import coffee_list, tea_list, syrup_list
from . import views

urlpatterns = [
    path('', views.index, name='index'),   
    path('coffee/', coffee_list, name='coffee_list'),
    path('tea/', tea_list, name='tea_list'),
    path('syrup/', syrup_list, name='syrup_list'),
]
