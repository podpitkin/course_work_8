from django.conf import settings
from django.db import models


class TelegramProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_profile',
        verbose_name='Пользователь',
    )
    chat_id = models.CharField(
        max_length=50,
        verbose_name='Telegram chat_id',
        help_text='Идентификатор пользователя в Telegram '
                  'для отправки напоминаний о привычках',
    )

    class Meta:
        verbose_name = 'Telegram-профиль'
        verbose_name_plural = 'Telegram-профили'

    def __str__(self):
        return f'{self.user.username}: {self.chat_id}'
