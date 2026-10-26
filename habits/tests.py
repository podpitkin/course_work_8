from datetime import time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from habits.models import Habit, TelegramProfile
from habits.tasks import send_habit_reminders
from habits.validators import (
    validate_duration,
    validate_periodicity,
    validate_pleasant_habit,
    validate_related_habit,
    validate_reward_and_related_habit,
)


class HabitModelTests(TestCase):
    """ Тесты модели Habit """

    def setUp(self):
        self.user = User.objects.create_user(
            username='habit_user',
            password='testpass123',
        )
        self.habit = Habit.objects.create(
            user=self.user,
            place='Дом',
            time=time(8, 0),
            action='Утренняя зарядка',
            duration=60,
        )

    def test_habit_fields(self):
        self.assertEqual(self.habit.user, self.user)
        self.assertEqual(self.habit.place, 'Дом')
        self.assertEqual(self.habit.action, 'Утренняя зарядка')
        self.assertEqual(self.habit.time, time(8, 0))
        self.assertEqual(self.habit.duration, 60)
        self.assertFalse(self.habit.is_pleasant)
        self.assertIsNone(self.habit.related_habit)
        self.assertEqual(self.habit.periodicity, 1)
        self.assertEqual(self.habit.reward, '')
        self.assertFalse(self.habit.is_public)

    def test_habit_str(self):
        self.assertEqual(str(self.habit), 'Утренняя зарядка (habit_user)')


class TelegramProfileModelTests(TestCase):
    """ Тесты модели TelegramProfile """

    def setUp(self):
        self.user = User.objects.create_user(
            username='telegram_user',
            password='testpass123',
        )
        self.profile = TelegramProfile.objects.create(
            user=self.user,
            chat_id='123456',
        )

    def test_profile_fields(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.chat_id, '123456')

    def test_profile_str(self):
        self.assertEqual(str(self.profile), 'telegram_user: 123456')


class ValidatorTests(TestCase):
    """ Тесты валидаторов привычек """

    def setUp(self):
        self.user = User.objects.create_user(
            username='validator_user',
            password='testpass123',
        )

    def test_reward_and_related_habit_together_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_reward_and_related_habit({
                'reward': 'Сладость',
                'related_habit': object(),
            })

    def test_reward_only_is_valid(self):
        self.assertIsNone(validate_reward_and_related_habit({'reward': 'Сладость'}))

    def test_duration_more_than_120_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_duration(121)

    def test_duration_120_is_valid(self):
        self.assertIsNone(validate_duration(120))

    def test_related_habit_must_be_pleasant(self):
        not_pleasant = Habit.objects.create(
            user=self.user,
            place='Офис',
            time=time(9, 0),
            action='Чтение',
            duration=60,
            is_pleasant=False,
        )
        with self.assertRaises(serializers.ValidationError):
            validate_related_habit(not_pleasant)

    def test_related_habit_pleasant_is_valid(self):
        pleasant = Habit.objects.create(
            user=self.user,
            place='Парк',
            time=time(10, 0),
            action='Прогулка',
            duration=120,
            is_pleasant=True,
        )
        self.assertIsNone(validate_related_habit(pleasant))

    def test_pleasant_habit_with_reward_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_pleasant_habit({'is_pleasant': True, 'reward': 'Сладость'})

    def test_pleasant_habit_with_related_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_pleasant_habit({'is_pleasant': True, 'related_habit': object()})

    def test_periodicity_more_than_7_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_periodicity(8)

    def test_periodicity_less_than_1_raises(self):
        with self.assertRaises(serializers.ValidationError):
            validate_periodicity(0)

    def test_periodicity_valid(self):
        self.assertIsNone(validate_periodicity(7))


class RegisterAPITests(APITestCase):
    """ Тесты регистрации пользователя """

    def test_register_creates_user(self):
        response = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertNotIn('password', response.data)

    def test_register_short_password_rejected(self):
        response = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'password': 'short'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenAPITests(APITestCase):
    """ Тесты JWT-авторизации """

    def setUp(self):
        self.user = User.objects.create_user(
            username='token_user',
            password='testpass123',
        )

    def test_token_obtain_pair(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'token_user', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_obtain_wrong_password(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'token_user', 'password': 'wrongpass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HabitAPITests(APITestCase):
    """ Тесты CRUD привычек """

    def setUp(self):
        self.user = User.objects.create_user(
            username='api_user',
            password='testpass123',
        )
        self.other_user = User.objects.create_user(
            username='other_user',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
        self.habit = Habit.objects.create(
            user=self.user,
            place='Дом',
            time=time(8, 0),
            action='Зарядка',
            duration=60,
        )
        self.other_habit = Habit.objects.create(
            user=self.other_user,
            place='Офис',
            time=time(9, 0),
            action='Чужое дело',
            duration=30,
        )

    def test_list_habits_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_habits_returns_only_own(self):
        response = self.client.get('/api/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'Зарядка')

    def test_create_habit(self):
        data = {
            'place': 'Парк',
            'time': '10:00:00',
            'action': 'Прогулка',
            'duration': 120,
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.filter(user=self.user).count(), 2)

    def test_create_habit_duration_greater_than_120_rejected(self):
        data = {
            'place': 'Парк',
            'time': '10:00:00',
            'action': 'Прогулка',
            'duration': 200,
        }
        response = self.client.post('/api/habits/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_see_other_habit_detail(self):
        response = self.client.get(f'/api/habits/{self.other_habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_habit(self):
        response = self.client.patch(
            f'/api/habits/{self.habit.id}/',
            {'place': 'Офис'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.place, 'Офис')

    def test_delete_own_habit(self):
        response = self.client.delete(f'/api/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=self.habit.id).exists())


class PublicHabitAPITests(APITestCase):
    """ Тесты списка публичных привычек """

    def setUp(self):
        self.user = User.objects.create_user(
            username='public_user',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
        self.public_habit = Habit.objects.create(
            user=self.user,
            place='Зал',
            time=time(18, 0),
            action='Тренировка',
            duration=90,
            is_public=True,
        )
        self.private_habit = Habit.objects.create(
            user=self.user,
            place='Дом',
            time=time(7, 0),
            action='Завтрак',
            duration=60,
            is_public=False,
        )

    def test_public_habits_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/public-habits/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_public_habits_returns_public_only(self):
        response = self.client.get('/api/public-habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actions = [item['action'] for item in response.data['results']]
        self.assertIn('Тренировка', actions)
        self.assertNotIn('Завтрак', actions)


class TelegramProfileAPITests(APITestCase):
    """ Тесты Telegram-профиля пользователя """

    def setUp(self):
        self.user = User.objects.create_user(
            username='profile_user',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/telegram-profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_creates_empty_profile(self):
        response = self.client.get('/api/telegram-profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(TelegramProfile.objects.filter(user=self.user).exists())

    def test_update_profile(self):
        response = self.client.put(
            '/api/telegram-profile/',
            {'chat_id': '123456789'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            TelegramProfile.objects.get(user=self.user).chat_id,
            '123456789',
        )


class SendHabitRemindersTaskTests(TestCase):
    """ Тесты Celery-задачи рассылки напоминаний """

    def setUp(self):
        self.user = User.objects.create_user(
            username='task_user',
            password='testpass123',
        )
        TelegramProfile.objects.create(user=self.user, chat_id='999888')
        now = timezone.localtime()
        self.habit = Habit.objects.create(
            user=self.user,
            place='Дом',
            time=time(now.hour, now.minute),
            action='Зарядка',
            duration=60,
        )

    @override_settings(TELEGRAM_BOT_TOKEN='test-token')
    @patch('habits.tasks.requests.post')
    def test_task_sends_message_to_chat(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        send_habit_reminders()
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['chat_id'], '999888')
        self.assertIn('Зарядка', payload['text'])

    @override_settings(TELEGRAM_BOT_TOKEN='')
    @patch('habits.tasks.requests.post')
    def test_task_skips_without_token(self, mock_post):
        send_habit_reminders()
        mock_post.assert_not_called()

    @patch('habits.tasks.requests.post')
    def test_task_skips_habit_without_telegram_profile(self, mock_post):
        other_user = User.objects.create_user(
            username='no_tg_user',
            password='testpass123',
        )
        now = timezone.localtime()
        Habit.objects.create(
            user=other_user,
            place='Дом',
            time=time(now.hour, now.minute),
            action='Без профиля',
            duration=60,
        )
        send_habit_reminders()
        mock_post.assert_not_called()

    @override_settings(TELEGRAM_BOT_TOKEN='test-token')
    @patch('habits.tasks.requests.post')
    def test_task_respects_periodicity(self, mock_post):
        other_user = User.objects.create_user(
            username='periodic_user',
            password='testpass123',
        )
        TelegramProfile.objects.create(user=other_user, chat_id='111222')
        now = timezone.localtime()
        habit = Habit.objects.create(
            user=other_user,
            place='Зал',
            time=time(now.hour, now.minute),
            action='Тренировка',
            duration=90,
            periodicity=2,
        )
        # Переносим дату создания на 1 день назад:
        # days_since_created = 1, 1 % 2 != 0 -> напоминание не должно уйти.
        Habit.objects.filter(pk=habit.pk).update(
            created_at=timezone.now() - timedelta(days=1),
        )
        send_habit_reminders()
        mock_post.assert_not_called()