from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import AllowAny

from habits.models import Habit, TelegramProfile
from habits.serializers import HabitSerializer, TelegramProfileSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """ Регистрация пользователя """

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class HabitViewSet(viewsets.ModelViewSet):
    """ CRUD привычек пользователя """

    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    """ Список публичных привычек  """

    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)

class TelegramProfileView(generics.RetrieveUpdateAPIView):
    """ Просмотр и обновление Telegram-профиля текущего пользователя """

    serializer_class = TelegramProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        obj, _ = TelegramProfile.objects.get_or_create(user=self.request.user)
        return obj
