
from django.urls import path
from .views import (
    coffee_list,
    tea_list, 
    syrup_list,
    delivery_info,
    product_search,
    coffee_detail,
    tea_detail,
    syrup_detail,
    add_to_cart,
    cart_detail,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    order_success,
    checkout,
    order_management
)
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

    path('cart/add/coffee/<int:product_id>/', add_to_cart, name='add_coffee_to_cart'),
    path('cart/add/tea/<int:product_id>/', add_to_cart, name='add_tea_to_cart'),
    path('cart/add/syrup/<int:product_id>/', add_to_cart, name='add_syrup_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),

    path('cart/checkout/', checkout, name='checkout'),
    path('cart/order/success/<int:order_id>/', order_success, name='order_success'),
    path('admin/orders/', order_management, name='order_management'),
   
]
