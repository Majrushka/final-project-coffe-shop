
from django.urls import path
from .views import coffee_list, tea_list, syrup_list, delivery_info, product_search, coffee_detail, tea_detail, syrup_detail
from . import views


urlpatterns = [
    path('', views.index, name='index'),   
    path('coffee/', coffee_list, name='coffee_list'),
    path('tea/', tea_list, name='tea_list'),
    path('syrup/', syrup_list, name='syrup_list'),
    path('delivery/', delivery_info, name='delivery_info'),
    path('coffee/<int:pk>/', coffee_detail, name='coffee_detail'),
    path('tea/<int:pk>/', tea_detail, name='tea_detail'),
    path('syrup/<int:pk>/', syrup_detail, name='syrup_detail'),
    path('search/', product_search, name='product_search'), 
   
]
