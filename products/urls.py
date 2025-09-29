
from django.urls import path
from .views import coffee_list, tea_list, syrup_list, delivery_info
# coffee_detail, tea_detail, syrup_detail
from . import views

urlpatterns = [
    path('', views.index, name='index'),   
    path('coffee/', coffee_list, name='coffee_list'),
    path('tea/', tea_list, name='tea_list'),
    path('syrup/', syrup_list, name='syrup_list'),
    path('delivery/', delivery_info, name='delivery_info'),
    # path('coffee/<uuid:pk>/', coffee_detail, name='coffee_detail'),
    # path('tea/<uuid:pk>/', tea_detail, name='tea_detail'),
    # path('syrup/<uuid:pk>/', syrup_detail, name='syrup_detail'),
    # path('search', views.search, name='search'),
]
