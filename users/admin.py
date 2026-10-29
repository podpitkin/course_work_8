from django.contrib import admin

from users.models import TelegramProfile


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    """Админка Telegram-профилей."""

    list_display = ('id', 'user', 'chat_id')
