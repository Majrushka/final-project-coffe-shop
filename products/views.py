from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Coffee, Tea, Syrup, Cart, CartItem, Order
from .forms import AddToCartForm, UpdateCartForm, OrderForm   
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ КОРЗИНЫ
def get_user_cart(user):
    """Получение активной корзины пользователя"""
    # Ищем все активные корзины пользователя
    active_carts = Cart.objects.filter(user=user, is_active=True)
    
    # Если найдено несколько активных корзин
    if active_carts.count() > 1:
        # Берем самую новую корзину
        cart = active_carts.order_by('-created_at').first()
        # Деактивируем все остальные корзины
        active_carts.exclude(id=cart.id).update(is_active=False)
        return cart
    # Если найдена одна корзина
    elif active_carts.count() == 1:
        return active_carts.first()
    # Если нет активных корзин
    else:
        # Создаем новую корзину
        cart = Cart.objects.create(user=user, is_active=True)
        return cart

# СУЩЕСТВУЮЩИЕ ВЬЮШКИ (без изменений)
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
    
    # Определяем тип продукта из URL
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
            
            # Для сиропов граммы не нужны
            if product_type == 'syrup':
                grams = None
            
            # Проверяем доступность товара
            if not product.is_available:
                messages.error(request, 'Этот товар временно недоступен')
                return redirect(f'{product_type}_detail', pk=product_id)
            
            # Проверяем валидность веса для кофе/чая
            if product_type in ['coffee', 'tea'] and not grams:
                messages.error(request, 'Пожалуйста, выберите вес')
                return redirect(f'{product_type}_detail', pk=product_id)
            
            # Проверяем корректность веса
            if product_type == 'coffee' and grams not in [250, 500, 1000]:
                messages.error(request, 'Неверный вес для кофе')
                return redirect(f'{product_type}_detail', pk=product_id)
            elif product_type == 'tea' and grams not in [100, 500]:
                messages.error(request, 'Неверный вес для чая')
                return redirect(f'{product_type}_detail', pk=product_id)
            
            # Создаем или обновляем элемент корзины
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
            
            # Если AJAX запрос, возвращаем JSON
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
                # Создаем заказ
                order = form.save(commit=False)
                order.user = request.user
                order.cart = cart
                order.total_price = cart.total_price
                order.save()
                
                # Делаем корзину неактивной
                cart.is_active = False
                cart.save()
                
                # Новая корзина создастся автоматически при следующем обращении к get_user_cart()
                
                # Пытаемся отправить уведомление владельцу (если настроены email-настройки)
                try:
                    send_new_order_notification(order, cart)
                except Exception as e:
                    # Если отправка email не настроена, просто игнорируем ошибку
                    print(f"Не удалось отправить уведомление владельцу: {e}")
                
                messages.success(request, 'Ваш заказ успешно оформлен!')
                return redirect('order_success', order_id=order.id)
                
            except IntegrityError:
                messages.error(request, 'Произошла ошибка при создании заказа. Пожалуйста, попробуйте еще раз.')
                return redirect('cart_detail')
    else:
        # Предзаполняем форму данными пользователя, если они есть
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
    
    # Дополнительная проверка, что заказ принадлежит пользователю
    if order.user != request.user:
        messages.error(request, 'У вас нет доступа к этому заказу')
        return redirect('index')
        
    return render(request, 'products/cart/order_success.html', {'order': order})

# СТРАНИЦА УПРАВЛЕНИЯ ЗАКАЗАМИ ДЛЯ АДМИНИСТРАТОРА
@staff_member_required
def order_management(request):
    """Страница управления заказами для администратора"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status_filter,
    }
    return render(request, 'products/admin/order_management.html', context)

def send_order_confirmation_email(order, cart):
    """Отправка email с подтверждением заказа"""
    subject = f'Подтверждение заказа #{order.id}'
    
    # Формируем список товаров
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
        fail_silently=False,
    )

def send_new_order_notification(order, cart):
    """Отправка уведомления владельцу о новом заказе"""
    subject = f'Новый заказ #{order.id}'
    
    # Формируем список товаров
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
    
    Для обработки заказа перейдите в админку:
    http://127.0.0.1:8000/admin/products/order/{order.id}/
    """
    
    # Замените на email владельца
    owner_email = 'ваш-email@gmail.com'  # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ EMAIL
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [owner_email],
        fail_silently=False,
    )