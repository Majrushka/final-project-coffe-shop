import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from django.conf import settings

# Конфигурация
BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
API_URL = 'http://localhost:8000/api/customer-orders/'

class CoffeeShopBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
☕️ Добро пожаловать в бот кофейни!

Для получения информации о ваших последних заказах просто отправьте мне ваш номер телефона в формате:
+79123456789 (Россия)
+375291234567 (Беларусь)
80291234567 (Беларусь)
89123456789 (Россия)

Я покажу вам последние 5 заказов! 📦
        """
        await update.message.reply_text(welcome_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text.strip()
        chat_id = update.message.chat_id
        
        print(f"📩 Получено сообщение: '{user_message}' от {chat_id}")
        
        # Валидация номера телефона
        phone_number = self.normalize_phone_number(user_message)
        if not phone_number:
            await update.message.reply_text(
                "❌ Пожалуйста, введите корректный номер телефона.\n"
                "Например:\n"
                "+79123456789 (Россия)\n"
                "+375291234567 (Беларусь)\n"
                "80291234567 (Беларусь)\n"
                "89123456789 (Россия)"
            )
            return
        
        print(f"🔍 Поиск заказов для телефона: {phone_number}")
        
        # Запрос к API
        try:
            response = requests.post(
                API_URL,
                json={
                    'phone_number': phone_number,
                    'telegram_chat_id': chat_id
                },
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📡 API Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Найдено заказов: {len(data.get('orders', []))}")
                await self.send_orders_response(update, data)
            elif response.status_code == 404:
                await update.message.reply_text(
                    f"📭 Заказы для телефона {phone_number} не найдены."
                )
            else:
                print(f"❌ Ошибка API: {response.text}")
                await update.message.reply_text(
                    f"❌ Ошибка сервера: {response.status_code}. Попробуйте позже."
                )
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса: {e}")
            await update.message.reply_text(
                "❌ Ошибка соединения с сервером. Убедитесь, что запущен Django сервер."
            )
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            await update.message.reply_text(
                "❌ Произошла непредвиденная ошибка."
            )
    
    async def send_orders_response(self, update: Update, data):
        orders = data.get('orders', [])
        
        if not orders:
            await update.message.reply_text(
                f"📭 Заказы для телефона {data.get('phone_number')} не найдены."
            )
            return
        
        response_text = f"📦 Ваши последние заказы ({len(orders)} из 5):\n\n"
        
        for order in orders:
            response_text += f"🆔 Заказ #{order['order_id']}\n"
            response_text += f"📅 {order['created_at']}\n"
            response_text += f"📊 Статус: {order['status']}\n"
            response_text += f"💳 Сумма: {order['total_price']} руб.\n"
            response_text += "📋 Состав:\n"
            
            for item in order['items']:
                response_text += f"   • {item['product_name']} - {item['quantity']} шт. x {item['unit_price']} руб.\n"
            
            response_text += "\n" + "="*40 + "\n\n"
        
        if len(response_text) > 4096:
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response_text)
    
    def normalize_phone_number(self, phone):
        """Нормализация номера телефона (поддержка российских и белорусских номеров)"""
        # Удаляем все нецифровые символы кроме +
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        print(f"🔧 Нормализация номера: {phone}")
        
        # Российские номера
        if phone.startswith('8') and len(phone) == 11:
            result = '+7' + phone[1:]
        elif phone.startswith('7') and len(phone) == 11:
            result = '+' + phone
        elif phone.startswith('+7') and len(phone) == 12:
            result = phone
        
        # Белорусские номера
        elif phone.startswith('80') and len(phone) == 11:  # 8029...
            result = '+375' + phone[2:]
        elif phone.startswith('375') and len(phone) == 12:
            result = '+' + phone
        elif phone.startswith('+375') and len(phone) == 13:
            result = phone
        
        else:
            result = None
        
        print(f"🔧 Результат нормализации: {result}")
        return result
    
    def run(self):
        print("🤖 Бот запускается...")
        print(f"🔑 Токен: {BOT_TOKEN}")
        try:
            # Проверка подключения
            print("🔗 Подключение к Telegram...")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
        )
        except Exception as e:
            print(f"💥 Критическая ошибка: {e}")
            print("🔧 Возможные причины:")
            print("   - Неправильный токен бота")
            print("   - Бот заблокирован")
            print("   - Проблемы с интернет-соединением")
# Создание экземпляра бота
bot = CoffeeShopBot()