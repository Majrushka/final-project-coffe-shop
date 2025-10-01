from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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