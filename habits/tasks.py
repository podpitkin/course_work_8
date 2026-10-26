import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from habits.models import Habit

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = 'https://api.telegram.org/bot{token}/sendMessage'


def send_telegram_message(chat_id, text):
    """ Отправляет сообщение в Telegram через Bot API """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning('TELEGRAM_BOT_TOKEN не задан, сообщение не отправлено')
        return

    url = TELEGRAM_API_URL.format(token=settings.TELEGRAM_BOT_TOKEN)
    payload = {
        'chat_id': chat_id,
        'text': text,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error('Ошибка отправки сообщения в Telegram (chat_id=%s): %s', chat_id, exc)


@shared_task
def send_habit_reminders():
    """ Находит привычки, подлежащие напоминанию сейчас и отправляет уведомления """
    now = timezone.localtime()
    current_time = now.time()

    habits = Habit.objects.filter(
        time__hour=current_time.hour,
        time__minute=current_time.minute,
        user__telegram_profile__isnull=False,
    )

    for habit in habits:
        days_since_created = (now.date() - habit.created_at.date()).days
        if days_since_created % habit.periodicity != 0:
            continue

        chat_id = habit.user.telegram_profile.chat_id
        message = (
            f'Напоминание о привычке!\n'
            f'Действие: {habit.action}\n'
            f'Место: {habit.place}\n'
            f'Время: {habit.time:%H:%M}\n'
            f'Длительность: {habit.duration} сек.'
        )
        send_telegram_message(chat_id, message)
        logger.info('Отправлено напоминание для привычки id=%s пользователю %s', habit.id, habit.user.username)
