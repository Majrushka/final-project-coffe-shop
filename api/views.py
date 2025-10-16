from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from products.models import Order, TelegramUser
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def get_customer_orders(request):
    """
    API endpoint для получения последних 5 заказов по номеру телефона
    """
    phone_number = request.data.get('phone_number')
    telegram_chat_id = request.data.get('telegram_chat_id')
    
    if not phone_number:
        return Response(
            {'error': 'Phone number is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Нормализуем номер телефона (убираем все кроме цифр и +)
        normalized_phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        print(f"🔍 Поиск заказов для:")
        print(f"   Исходный номер: {phone_number}")
        print(f"   Нормализованный: {normalized_phone}")
        
        # Сохраняем/обновляем связь телефона с Telegram chat_id
        telegram_user, created = TelegramUser.objects.get_or_create(
            phone_number=normalized_phone,
            defaults={'telegram_chat_id': telegram_chat_id}
        )
        
        if not created and telegram_user.telegram_chat_id != telegram_chat_id:
            telegram_user.telegram_chat_id = telegram_chat_id
            telegram_user.save()
        
        # Нормализуем ВСЕ номера в базе для поиска
        all_orders = Order.objects.all()
        matching_orders = []
        
        for order in all_orders:
            # Нормализуем номер из базы
            order_phone_normalized = ''.join(c for c in order.phone if c.isdigit() or c == '+')
            if order_phone_normalized == normalized_phone:
                matching_orders.append(order)
        
        # Берем последние 5 заказов
        orders = sorted(matching_orders, key=lambda x: x.created_at, reverse=True)[:5]
        
        print(f"   Найдено заказов: {len(orders)}")
        
        if not orders:
            return Response({
                'message': f'Заказы для телефона {phone_number} не найдены',
                'orders': []
            }, status=status.HTTP_200_OK)
        
        orders_data = []
        for order in orders:
            order_data = {
                'order_id': order.id,
                'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
                'status': order.get_status_display(),
                'total_price': str(order.total_price),
                'items': []
            }
            
            # Получаем товары из корзины заказа
            cart_items = order.cart.items.all()
            for item in cart_items:
                item_data = {
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price)
                }
                order_data['items'].append(item_data)
            
            orders_data.append(order_data)
        
        return Response({
            'phone_number': phone_number,
            'total_orders_found': len(orders_data),
            'orders': orders_data
        })
        
    except Exception as e:
        logger.error(f"Error getting orders for {phone_number}: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )