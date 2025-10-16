from django.core.management.base import BaseCommand
from telegram_bot.bot import bot

class Command(BaseCommand):
    help = 'Run Telegram Bot'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Telegram Bot...')
        )
        bot.run()