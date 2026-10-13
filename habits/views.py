from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import AllowAny

from habits.models import Habit
from habits.serializers import HabitSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class HabitViewSet(viewsets.ModelViewSet):
    """CRUD привычек текущего пользователя."""

    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    """Список публичных привычек (только чтение)."""

    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)
