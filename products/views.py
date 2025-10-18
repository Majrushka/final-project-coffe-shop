from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Coffee, Tea, Syrup, Cart, CartItem, Order, TelegramUser
from .forms import AddToCartForm, UpdateCartForm, OrderForm

logger = logging.getLogger(__name__)

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def get_user_cart(user):
    """Получение активной корзины пользователя"""
    active_carts = Cart.objects.filter(user=user, is_active=True)
    
    if active_carts.count() > 1:
        cart = active_carts.order_by('-created_at').first()
        active_carts.exclude(id=cart.id).update(is_active=False)
        return cart
    elif active_carts.count() == 1:
        return active_carts.first()
    else:
        cart = Cart.objects.create(user=user, is_active=True)
        return cart

def normalize_phone(phone):
    """Нормализует номер телефона к стандартному формату"""
    import re
    digits = re.sub(r'\D', '', phone)
    
    if digits.startswith('375'):
        return '+' + digits
    elif digits.startswith('80'):
        return '+375' + digits[2:]
    elif len(digits) == 9 and digits.startswith(('29', '33', '44', '25')):
        return '+375' + digits
    else:
        return '+' + digits

def send_order_confirmation_email(order, cart):
    """Отправка email с подтверждением заказа"""
    try:
        subject = f'Подтверждение заказа #{order.id}'
        
        items_list = ""
        for item in cart.items.all():
            items_list += f"- {item.product_name}: {item.quantity} шт. x {item.unit_price} руб. = {item.total_price} руб.\n"
        
        message = f"""
        Уважаемый(ая) {order.first_name} {order.last_name}!

        Благодарим вас за заказ в нашем магазине!

        Детали заказа:
        Номер заказа: #{order.id}
        Дата заказа: {order.created_at.strftime('%d.%m.%Y %H:%M')}
        
        Состав заказа:
        {items_list}
        
        Общая сумма: {order.total_price} руб.
        
        Контактная информация:
        Телефон: {order.phone}
        Email: {order.email}
        
        Статус заказа: {order.get_status_display()}
        
        Мы свяжемся с вами в ближайшее время для уточнения деталей доставки.
        
        С уважением,
        Команда Fun Coffee
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )
        logger.info(f"✅ Email подтверждения отправлен для заказа #{order.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки email для заказа #{order.id}: {str(e)}")

def send_new_order_notification(order, cart):
    """Отправка уведомления владельцу о новом заказе"""
    try:
        subject = f'Новый заказ #{order.id}'
        
        items_list = ""
        for item in cart.items.all():
            items_list += f"- {item.product_name}: {item.quantity} шт. x {item.unit_price} руб. = {item.total_price} руб.\n"
        
        message = f"""
        ПОСТУПИЛ НОВЫЙ ЗАКАЗ!

        Детали заказа:
        Номер заказа: #{order.id}
        Дата заказа: {order.created_at.strftime('%d.%m.%Y %H:%M')}
        
        Информация о клиенте:
        Имя: {order.first_name} {order.last_name}
        Телефон: {order.phone}
        Email: {order.email}
        
        Состав заказа:
        {items_list}
        
        Общая сумма: {order.total_price} руб.
        
        Статус заказа: {order.get_status_display()}
        """
        
        owner_email = getattr(settings, 'OWNER_EMAIL', 'owner@example.com')
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [owner_email],
            fail_silently=True,
        )
        logger.info(f"✅ Уведомление владельцу отправлено для заказа #{order.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления владельцу: {str(e)}")

# API ДЛЯ TELEGRAM БОТА
@api_view(['POST'])
def customer_orders(request):
    """API для получения заказов клиента"""
    try:
        logger.info(f"📨 Получен запрос на поиск заказов. Данные: {request.data}")
        
        phone = request.data.get('phone')
        telegram_chat_id = request.data.get('telegram_chat_id')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        username = request.data.get('username')
        
        if not phone:
            logger.error("❌ Phone number is required")
            return Response({'error': 'Phone number is required'}, status=400)
        
        # Нормализация номера телефона
        normalized_phone = normalize_phone(phone)
        logger.info(f"🔧 Нормализация номера: {phone} -> {normalized_phone}")
        
        # ОБРАБОТКА TelegramUser - УПРОЩЕННЫЙ ПОДХОД
        if telegram_chat_id:
            try:
                logger.info(f"🔍 Обработка Telegram пользователя с chat_id: {telegram_chat_id}")
                
                # Сначала пытаемся найти существующего пользователя по chat_id
                existing_user_by_chat = TelegramUser.objects.filter(telegram_chat_id=telegram_chat_id).first()
                
                if existing_user_by_chat:
                    logger.info(f"✅ Найден пользователь по chat_id: {existing_user_by_chat}")
                    # Если нашли по chat_id - обновляем данные
                    existing_user_by_chat.phone_number = normalized_phone
                    existing_user_by_chat.first_name = first_name
                    existing_user_by_chat.last_name = last_name
                    existing_user_by_chat.username = username
                    existing_user_by_chat.save()
                    logger.info(f"📝 Обновлены данные пользователя")
                else:
                    # Если не нашли по chat_id, ищем по номеру телефона
                    existing_user_by_phone = TelegramUser.objects.filter(phone_number=normalized_phone).first()
                    
                    if existing_user_by_phone:
                        logger.info(f"✅ Найден пользователь по номеру телефона: {existing_user_by_phone}")
                        # Обновляем chat_id у существующего пользователя
                        existing_user_by_phone.telegram_chat_id = telegram_chat_id
                        existing_user_by_phone.first_name = first_name
                        existing_user_by_phone.last_name = last_name
                        existing_user_by_phone.username = username
                        existing_user_by_phone.save()
                        logger.info(f"📝 Обновлен chat_id пользователя")
                    else:
                        # Создаем нового пользователя
                        logger.info("🆕 Создание нового Telegram пользователя")
                        telegram_user = TelegramUser(
                            phone_number=normalized_phone,
                            telegram_chat_id=telegram_chat_id,
                            first_name=first_name,
                            last_name=last_name,
                            username=username
                        )
                        telegram_user.save()
                        logger.info(f"✅ Создан новый пользователь: {telegram_user}")
                        
            except IntegrityError as e:
                logger.warning(f"⚠️ IntegrityError: {str(e)}")
                # В случае ошибки уникальности - просто логируем и продолжаем
                logger.info("🔄 Пропускаем ошибку Telegram пользователя и продолжаем поиск заказов")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки Telegram пользователя: {str(e)}")
                # Продолжаем выполнение даже при ошибке
        
        # ПОИСК ЗАКАЗОВ (основная логика)
        logger.info(f"🔍 Поиск заказов для телефона: {normalized_phone}")
        
        try:
            orders = Order.objects.filter(phone=normalized_phone).order_by('-created_at')[:5]
            logger.info(f"📦 Найдено заказов: {orders.count()}")
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске заказов: {str(e)}")
            return Response({'error': 'Ошибка поиска заказов'}, status=500)
        
        if not orders.exists():
            logger.info(f"❌ Заказы не найдены для телефона: {normalized_phone}")
            return Response({'error': 'Заказы не найдены'}, status=404)
        
        orders_data = []
        for order in orders:
            try:
                order_data = {
                    'id': order.id,
                    'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
                    'total_price': str(order.total_price),
                    'status': order.get_status_display(),
                    'items': []
                }
                
                for item in order.cart.items.all():
                    order_data['items'].append({
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': str(item.unit_price),
                        'total_price': str(item.total_price)
                    })
                
                orders_data.append(order_data)
            except Exception as e:
                logger.error(f"❌ Ошибка обработки заказа #{order.id}: {str(e)}")
                continue
        
        logger.info(f"✅ Успешно возвращено {len(orders_data)} заказов")
        return Response({'orders': orders_data})
        
    except Exception as e:
        logger.error(f"❌ Общая ошибка в customer_orders: {str(e)}")
        return Response({'error': 'Внутренняя ошибка сервера'}, status=500)

# ОСНОВНЫЕ ВЬЮШКИ САЙТА
def index(request):
    coffees = Coffee.objects.all().order_by('-is_available')
    teas = Tea.objects.all().order_by('-is_available')
    syrups = Syrup.objects.all().order_by('-is_available')
    
    context = {
        'coffees': coffees,
        'teas': teas,
        'syrups': syrups,
    }
    
    return render(request, 'products/index.html', context)

def coffee_list(request):
    coffees = Coffee.objects.all().order_by('-is_available')
    paginator = Paginator(coffees, 4)
    page_number = request.GET.get('page', 1)
    coffees = paginator.get_page(page_number)
    return render(request, 'products/coffee_list.html', {"coffees": coffees})

def tea_list(request):
    teas = Tea.objects.all().order_by('-is_available')
    return render(request, 'products/tea_list.html', {"teas": teas})

def syrup_list(request):
    syrups = Syrup.objects.all().order_by('-is_available')
    return render(request, 'products/syrup_list.html', {"syrups": syrups})

def delivery_info(request):
    return render(request, 'products/delivery_info.html')

def coffee_detail(request, pk):
    coffee = get_object_or_404(Coffee, pk=pk)
    form = AddToCartForm(product_type='coffee')
    return render(request, 'products/coffee_detail.html', {
        'coffee': coffee,
        'form': form
    })

def tea_detail(request, pk):
    tea = get_object_or_404(Tea, pk=pk)
    form = AddToCartForm(product_type='tea')
    return render(request, 'products/tea_detail.html', {
        'tea': tea,
        'form': form
    })

def syrup_detail(request, pk):
    syrup = get_object_or_404(Syrup, pk=pk)
    form = AddToCartForm(product_type='syrup')
    return render(request, 'products/syrup_detail.html', {
        'syrup': syrup,
        'form': form
    })

def product_search(request):
    query = request.GET.get('q', '').strip().title()
    results = []
    
    if query in ['кофе', 'coffee']:
        return redirect('coffee_list')
    elif query in ['чай', 'чаи', 'tea']:
        return redirect('tea_list')
    elif query in ['сироп', 'сиропы', 'syrup']:
        return redirect('syrup_list')
    
    results = []

    if query:
        coffee_results = Coffee.objects.filter(name__iexact=query)
        tea_results = Tea.objects.filter(name__iexact=query)
        syrup_results = Syrup.objects.filter(name__iexact=query)
        
        results = list(coffee_results) + list(tea_results) + list(syrup_results)
        
        if not results:
            coffee_results = Coffee.objects.filter(name__icontains=query)
            tea_results = Tea.objects.filter(name__icontains=query)
            syrup_results = Syrup.objects.filter(name__icontains=query)
            results = list(coffee_results) + list(tea_results) + list(syrup_results)
        
        if len(results) == 1:
            product = results[0]
            if isinstance(product, Coffee):
                return redirect('coffee_detail', pk=product.pk)
            elif isinstance(product, Tea):
                return redirect('tea_detail', pk=product.pk)
            elif isinstance(product, Syrup):
                return redirect('syrup_detail', pk=product.pk)
    
    return render(request, 'products/search_results.html', {
        'results': results,
        'query': query,
    })

# ВЬЮШКИ КОРЗИНЫ (ТОЛЬКО ДЛЯ АВТОРИЗОВАННЫХ)
@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    
    if 'coffee' in request.path:
        product_type = 'coffee'
        product = get_object_or_404(Coffee, id=product_id, is_available=True)
    elif 'tea' in request.path:
        product_type = 'tea'
        product = get_object_or_404(Tea, id=product_id, is_available=True)
    elif 'syrup' in request.path:
        product_type = 'syrup'
        product = get_object_or_404(Syrup, id=product_id, is_available=True)
    else:
        messages.error(request, 'Неверный тип товара')
        return redirect('index')
    
    cart = get_user_cart(request.user)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST, product_type=product_type)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            grams = form.cleaned_data['grams']
            
            if product_type == 'syrup':
                grams = None
            
            if not product.is_available:
                messages.error(request, 'Этот товар временно недоступен')
                return redirect(f'{product_type}_detail', pk=product_id)
            
            if product_type in ['coffee', 'tea'] and not grams:
                messages.error(request, 'Пожалуйста, выберите вес')
                return redirect(f'{product_type}_detail', pk=product_id)
            
            if product_type == 'coffee' and grams not in [250, 500, 1000]:
                messages.error(request, 'Неверный вес для кофе')
                return redirect(f'{product_type}_detail', pk=product_id)
            elif product_type == 'tea' and grams not in [100, 500]:
                messages.error(request, 'Неверный вес для чая')
                return redirect(f'{product_type}_detail', pk=product_id)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_type=product_type,
                product_id=product_id,
                grams=grams,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, f'Количество товара обновлено в корзине')
            else:
                messages.success(request, f'Товар "{product.name}" добавлен в корзину')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': 'Товар добавлен в корзину',
                    'cart_total_items': cart.total_items
                })
            
            return redirect('index')
    
    return redirect(f'{product_type}_detail', pk=product_id)

@login_required
def cart_detail(request):
    """Просмотр корзины"""
    cart = get_user_cart(request.user)
    return render(request, 'products/cart/cart_detail.html', {'cart': cart})

@login_required
def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    cart = get_user_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    if request.method == 'POST':
        form = UpdateCartForm(request.POST, instance=cart_item)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            if quantity == 0:
                product_name = cart_item.product_name
                cart_item.delete()
                messages.success(request, f'Товар "{product_name}" удален из корзины')
            else:
                form.save()
                messages.success(request, 'Количество товара обновлено')
    
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart = get_user_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product_name
    cart_item.delete()
    messages.success(request, f'Товар "{product_name}" удален из корзины')
    return redirect('cart_detail')

@login_required
def clear_cart(request):
    """Очистка всей корзины"""
    cart = get_user_cart(request.user)
    cart.items.all().delete()
    messages.success(request, 'Корзина очищена')
    return redirect('cart_detail')

@login_required
def checkout(request):
    """Оформление заказа"""
    cart = get_user_cart(request.user)
    
    if not cart.items.exists():
        messages.error(request, 'Ваша корзина пуста')
        return redirect('cart_detail')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = form.save(commit=False)
                order.user = request.user
                order.cart = cart
                order.total_price = cart.total_price
                order.save()
                
                cart.is_active = False
                cart.save()
                
                try:
                    send_order_confirmation_email(order, cart)
                    send_new_order_notification(order, cart)
                except Exception as e:
                    logger.error(f"Ошибка отправки email: {str(e)}")
                
                messages.success(request, 'Ваш заказ успешно оформлен!')
                return redirect('order_success', order_id=order.id)
                
            except IntegrityError:
                messages.error(request, 'Произошла ошибка при создании заказа. Пожалуйста, попробуйте еще раз.')
                return redirect('cart_detail')
    else:
        initial_data = {}
        if request.user.first_name:
            initial_data['first_name'] = request.user.first_name
        if request.user.last_name:
            initial_data['last_name'] = request.user.last_name
        if request.user.email:
            initial_data['email'] = request.user.email
            
        form = OrderForm(initial=initial_data)
    
    return render(request, 'products/cart/checkout.html', {
        'cart': cart,
        'form': form
    })

@login_required
def order_success(request, order_id):
    """Страница успешного оформления заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.user != request.user:
        messages.error(request, 'У вас нет доступа к этому заказу')
        return redirect('index')
        
    return render(request, 'products/cart/order_success.html', {'order': order})

# СТРАНИЦА УПРАВЛЕНИЯ ЗАКАЗАМИ ДЛЯ АДМИНИСТРАТОРА
@staff_member_required
def order_management(request):
    """Страница управления заказами для администратора"""
    orders = Order.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status_filter,
    }
    return render(request, 'products/admin/order_management.html', context)