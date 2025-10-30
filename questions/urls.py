# questions/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"domains", views.DomainViewSet, basename="domain")
router.register(r"topics", views.TopicViewSet, basename="topic")
router.register(r"questions", views.QuestionViewSet, basename="question")

urlpatterns = router.urls
