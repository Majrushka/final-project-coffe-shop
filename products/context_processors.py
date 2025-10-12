from .models import Cart

def cart_context(request):
    """
    Добавляет корзину в контекст всех шаблонов
    """
    cart = None
    if request.user.is_authenticated:
        # Ищем все активные корзины пользователя
        active_carts = Cart.objects.filter(user=request.user, is_active=True)
        
        # Если найдено несколько активных корзин
        if active_carts.count() > 1:
            # Берем самую новую корзину
            cart = active_carts.order_by('-created_at').first()
            # Деактивируем все остальные корзины
            active_carts.exclude(id=cart.id).update(is_active=False)
        # Если найдена одна корзина
        elif active_carts.count() == 1:
            cart = active_carts.first()
        # Если нет активных корзин - создавать новую не нужно в контекстном процессоре
        # Новая корзина создастся при первом добавлении товара
    
    return {
        'cart': cart
    }