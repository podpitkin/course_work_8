from rest_framework import serializers


def validate_reward_and_related_habit(attrs):
    """ Нельзя заполнять одновременно вознаграждение и связанную привычку """
    reward = attrs.get('reward')
    related_habit = attrs.get('related_habit')
    if reward and related_habit:
        raise serializers.ValidationError(
            'Нельзя заполнять одновременно вознаграждение и связанную привычку. '
            'Можно заполнить только одно из двух полей.'
        )


def validate_duration(value):
    """ Время выполнения должно быть не больше 120 секунд """
    if value > 120:
        raise serializers.ValidationError(
            'Время на выполнение привычки не должно превышать 120 секунд.'
        )


def validate_related_habit(value):
    """ В связанные привычки могут попадать только приятные привычки """
    if value is not None and not value.is_pleasant:
        raise serializers.ValidationError(
            'В связанные привычки могут попадать только привычки '
            'с признаком приятной привычки.'
        )


def validate_pleasant_habit(attrs):
    """ У приятной привычки не может быть вознаграждения или связанной привычки """
    is_pleasant = attrs.get('is_pleasant')
    if is_pleasant and (attrs.get('reward') or attrs.get('related_habit')):
        raise serializers.ValidationError(
            'У приятной привычки не может быть вознаграждения или связанной привычки.'
        )


def validate_periodicity(value):
    """ Нельзя выполнять привычку реже, чем 1 раз в 7 дней """
    if value > 7:
        raise serializers.ValidationError(
            'Нельзя выполнять привычку реже, чем 1 раз в 7 дней.'
        )
    if value < 1:
        raise serializers.ValidationError(
            'Периодичность должна быть не меньше 1 дня.'
        )
