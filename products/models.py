from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Product(models.Model):
    """Базовая модель продукта"""
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание', default='')
    is_available = models.BooleanField(default=True, verbose_name='В наличии')
    
    class Meta:
        abstract = True

class Coffee(Product):
    
    COFFEE_TYPE_CHOICES = [
        ('arabica', 'Арабика'),
        ('robusta', 'Робуста'),
        ('blend', 'Смесь'),
    ]
    
    GRAMS_CHOICES = [
        (250, '250 г'),
        (500, '500 г'),
        (1000, '1000 г'),
    ]

    image = models.ImageField(
        upload_to='coffee_images/',
        verbose_name='Изображение',
        blank=True,
        null=True
    )
    
    # Специфические характеристики кофе
    coffee_type = models.CharField(
        max_length=10,
        choices=COFFEE_TYPE_CHOICES,
        verbose_name='Сорт кофе',
        default='arabica'
    )
    
    # Цены в зависимости от веса
    price_250g = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена за 250 г',
        default=0.00
    )
    price_500g = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена за 500 г',
        default=0.00
    )
    price_1000g = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена за 1000 г',
        default=0.00
    )
    
    # Характеристики вкуса (шкала 1-5)
    acidity = models.PositiveSmallIntegerField(
        verbose_name='Кислотность (1-5)',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Оценка от 1 до 5',
        default=3
    )
    bitterness = models.PositiveSmallIntegerField(
        verbose_name='Горчинка (1-5)',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Оценка от 1 до 5',
        default=3
    )
    intensity = models.PositiveSmallIntegerField(
        verbose_name='Насыщенность (1-5)',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Оценка от 1 до 5',
        default=3
    )

    def get_price(self, grams):
        """Возвращает цену для указанного веса"""
        price_map = {
            250: self.price_250g,
            500: self.price_500g,
            1000: self.price_1000g
        }
        return price_map.get(grams)

    def __str__(self):
        return f"{self.name} ({self.get_coffee_type_display()})"

    class Meta:
        verbose_name = 'Кофе'
        verbose_name_plural = 'Кофе'


class Tea(Product):
    
    TEA_TYPE_CHOICES = [
        ('black', 'Черный'),
        ('green', 'Зеленый'),
    ]
    
    GRAMS_CHOICES = [
        (100, '100 г'),
        (500, '500 г'),
    ]

    image = models.ImageField(
        upload_to='tea_images/',
        verbose_name='Изображение',
        blank=True,
        null=True
    )
    
    # Специфические характеристики чая
    tea_type = models.CharField(
        max_length=10,
        choices=TEA_TYPE_CHOICES,
        verbose_name='Вид чая',
        default='black'
    )
    
    # Цены в зависимости от веса
    price_100g = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена за 100 г',
        default=0.00
    )
    price_500g = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена за 500 г',
        default=0.00
    )

    def get_price(self, grams):
        """Возвращает цену для указанного веса"""
        price_map = {
            100: self.price_100g,
            500: self.price_500g
        }
        return price_map.get(grams)

    def __str__(self):
        return f"{self.name} ({self.get_tea_type_display()})"

    class Meta:
        verbose_name = 'Чай'
        verbose_name_plural = 'Чай'


class Syrup(Product):
   
    MANUFACTURER_CHOICES = [
        ('manufacturer1', 'Monin'),
        ('manufacturer2', 'Barinoff'),
    ]
    
    # Специфические характеристики сиропа
    manufacturer = models.CharField(
        max_length=20,
        choices=MANUFACTURER_CHOICES,
        verbose_name='Производитель',
        default='manufacturer1'
    )

    image = models.ImageField(
        upload_to='syrup_images/',
        verbose_name='Изображение',
        blank=True,
        null=True
    )
    
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена',
        default=0.00
    )

    def __str__(self):
        return f"{self.name} ({self.get_manufacturer_display()})"

    class Meta:
        verbose_name = 'Сироп'
        verbose_name_plural = 'Сиропы'


# МОДЕЛИ КОРЗИНЫ (ТОЛЬКО ДЛЯ АВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ)
class Cart(models.Model):
    user = models.ForeignKey( 
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активная корзина')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def __str__(self):
        status = "активная" if self.is_active else "неактивная"
        return f"Корзина {self.id} ({status}) - {self.user.username}"
    
    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class CartItem(models.Model):
    PRODUCT_TYPES = [
        ('coffee', 'Кофе'),
        ('tea', 'Чай'),
        ('syrup', 'Сироп'),
    ]
    
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        related_name='items', 
        verbose_name='Корзина'
    )
    
    # Поля для связи с разными типами продуктов
    product_type = models.CharField(
        max_length=10, 
        choices=PRODUCT_TYPES, 
        verbose_name='Тип товара'
    )
    product_id = models.PositiveIntegerField(verbose_name='ID товара')
    
    grams = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name='Вес (граммы)',
        help_text='Только для кофе и чая'
    )
    
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    
    @property
    def product(self):
        """Возвращает объект продукта в зависимости от типа"""
        if self.product_type == 'coffee':
            return Coffee.objects.filter(id=self.product_id).first()
        elif self.product_type == 'tea':
            return Tea.objects.filter(id=self.product_id).first()
        elif self.product_type == 'syrup':
            return Syrup.objects.filter(id=self.product_id).first()
        return None
    
    @property
    def unit_price(self):
        """Возвращает цену за единицу товара"""
        product = self.product
        if not product:
            return 0
        
        if self.product_type == 'coffee' and self.grams:
            return product.get_price(self.grams) or 0
        elif self.product_type == 'tea' and self.grams:
            return product.get_price(self.grams) or 0
        elif self.product_type == 'syrup':
            return product.price or 0
        return 0
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity
    
    @property
    def product_name(self):
        product = self.product
        if product:
            if self.product_type == 'coffee' and self.grams:
                return f"{product.name} ({self.grams}г)"
            elif self.product_type == 'tea' and self.grams:
                return f"{product.name} ({self.grams}г)"
            else:
                return str(product)
        return "Товар не найден"
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
    
    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ['cart', 'product_type', 'product_id', 'grams']

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('confirmed', 'Подтвержден'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    # Связь один-ко-многим с пользователем
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь',
        null=True, 
        blank=True
    )
    
    # Связь один-ко-многим с корзиной
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        verbose_name='Корзина'
    )
    
    # Контактная информация
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Электронная почта')
    
    # Статус и даты
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending', 
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Общая сумма'
    )
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.first_name} {self.last_name} ({self.status})"
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

class TelegramUser(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь',
        null=True,
        blank=True
    )
    phone_number = models.CharField(
        max_length=20, 
        verbose_name='Номер телефона',
        unique=True
    )
    telegram_chat_id = models.BigIntegerField(
        verbose_name='ID чата Telegram',
        unique=True
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    def __str__(self):
        return f"{self.phone_number} (Chat ID: {self.telegram_chat_id})"
    
    class Meta:
        verbose_name = 'Пользователь Telegram'
        verbose_name_plural = 'Пользователи Telegram'