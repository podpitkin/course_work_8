from django.conf import settings
from django.db import models


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
        verbose_name='Пользователь',
    )
    place = models.CharField(
        max_length=255,
        verbose_name='Место',
        help_text='Место, в котором необходимо выполнять привычку',
    )
    time = models.TimeField(
        verbose_name='Время',
        help_text='Время, когда необходимо выполнять привычку',
    )
    action = models.CharField(
        max_length=255,
        verbose_name='Действие',
        help_text='Действие, которое представляет собой привычка',
    )
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name='Признак приятной привычки',
        help_text='Привычка, которую можно привязать к выполнению полезной привычки',
    )
    related_habit = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_to',
        verbose_name='Связанная привычка',
        help_text='Привычка, которая связана с другой привычкой. '
                  'Указывается для полезных привычек, но не для приятных',
    )
    periodicity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Периодичность (в днях)',
        help_text='Периодичность выполнения привычки для напоминания в днях',
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Вознаграждение',
        help_text='Чем пользователь должен себя вознаградить после выполнения',
    )
    duration = models.PositiveSmallIntegerField(
        verbose_name='Время на выполнение (в секундах)',
        help_text='Время, которое предположительно потратит пользователь на выполнение привычки',
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Признак публичности',
        help_text='Привычки можно публиковать в общий доступ, '
                  'чтобы другие пользователи могли брать в пример чужие привычки',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['id']

    def __str__(self):
        return f'{self.action} ({self.user})'

class TelegramProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='telegram_profile',
        verbose_name='Пользователь',
    )
    chat_id = models.CharField(
        max_length=64,
        verbose_name='Telegram chat_id',
        help_text='Идентификатор чата пользователя в Telegram '
                  'для отправки напоминаний о привычках',
    )

    class Meta:
        verbose_name = 'Telegram-профиль'
        verbose_name_plural = 'Telegram-профили'

    def __str__(self):
        return f'{self.user.username}: {self.chat_id}'
