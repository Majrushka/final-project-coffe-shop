from django.contrib import admin
from .models import Coffee, Tea, Syrup, Order, Cart, CartItem

admin.site.register(Coffee)
admin.site.register(Tea)
admin.site.register(Syrup)

class CartItemInline(admin.TabularInline):
    model = CartItem
    readonly_fields = ['product_type', 'product_id', 'grams', 'quantity', 'unit_price', 'total_price']
    extra = 0
    can_delete = False

    def unit_price(self, obj):
        return f"{obj.unit_price} руб."
    unit_price.short_description = 'Цена за единицу'

    def total_price(self, obj):
        return f"{obj.total_price} руб."
    total_price.short_description = 'Общая стоимость'

class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_active', 'created_at', 'total_price_display']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['total_price_display']
    inlines = [CartItemInline]

    def total_price_display(self, obj):
        return f"{obj.total_price} руб."
    total_price_display.short_description = 'Общая сумма'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'phone', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'order_items_display']
    # УБРАТЬ: inlines = [CartItemInline]  ← ЭТУ СТРОКУ УБРАТЬ

    def order_items_display(self, obj):
        """Отображает состав заказа в админке"""
        items = obj.cart.items.all()  # Получаем товары через корзину
        if not items:
            return "Заказ пуст"
        
        items_list = []
        for item in items:
            items_list.append(f"{item.product_name} - {item.quantity} шт. x {item.unit_price} руб. = {item.total_price} руб.")
        
        return "\n".join(items_list)
    order_items_display.short_description = 'Состав заказа'

admin.site.register(Cart, CartAdmin)