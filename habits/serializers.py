from django.contrib.auth.models import User
from rest_framework import serializers

from habits.models import Habit
from habits.validators import (
    validate_duration,
    validate_periodicity,
    validate_pleasant_habit,
    validate_related_habit,
    validate_reward_and_related_habit,
)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для регистрации."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор привычки."""

    class Meta:
        model = Habit
        fields = (
            'id',
            'place',
            'time',
            'action',
            'is_pleasant',
            'related_habit',
            'periodicity',
            'reward',
            'duration',
            'is_public',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        validate_reward_and_related_habit(attrs)
        validate_pleasant_habit(attrs)
        return attrs

    def validate_duration(self, value):
        return validate_duration(value)

    def validate_related_habit(self, value):
        return validate_related_habit(value)

    def validate_periodicity(self, value):
        return validate_periodicity(value)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
