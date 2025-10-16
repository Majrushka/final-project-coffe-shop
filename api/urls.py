from django.urls import path
from . import views

urlpatterns = [
    path('customer-orders/', views.get_customer_orders, name='customer-orders'),
]