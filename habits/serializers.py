from rest_framework import serializers

from habits.models import Habit
from habits.validators import (
    validate_duration,
    validate_periodicity,
    validate_pleasant_habit,
    validate_related_habit,
    validate_reward_and_related_habit,
)


class HabitSerializer(serializers.ModelSerializer):

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
        validate_duration(value)
        return value

    def validate_related_habit(self, value):
        validate_related_habit(value)
        return value

    def validate_periodicity(self, value):
        validate_periodicity(value)
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
