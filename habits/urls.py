from django.urls import include, path
from rest_framework.routers import DefaultRouter
from habits.views import HabitViewSet, PublicHabitListView


router = DefaultRouter()
router.register('habits', HabitViewSet, basename='habit')

urlpatterns = [
    path('public-habits/', PublicHabitListView.as_view(), name='public-habits'),
    path('', include(router.urls)),
]
