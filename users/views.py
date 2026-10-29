from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny

from users.models import TelegramProfile
from users.serializers import TelegramProfileSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class TelegramProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и обновление Telegram-профиля текущего пользователя."""

    serializer_class = TelegramProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        obj, _ = TelegramProfile.objects.get_or_create(user=self.request.user)
        return obj
