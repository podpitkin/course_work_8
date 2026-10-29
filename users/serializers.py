from django.contrib.auth.models import User
from rest_framework import serializers

from users.models import TelegramProfile


class UserSerializer(serializers.ModelSerializer):
    """ Сериализатор пользователя """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TelegramProfileSerializer(serializers.ModelSerializer):
    """ Сериализатор Telegram-профиля """

    class Meta:
        model = TelegramProfile
        fields = ('id', 'chat_id')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
