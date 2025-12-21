from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# router.register(r"signup", views.SignupView, basename='signup')
# router.register(r"signin", views.SigninView, basename='signin')
router.register(r"", views.UserViewSet, basename='users')

urlpatterns = router.urls
# urlpatterns = [
#     path('signup/', SignupView.as_view(), name='signup'),
#     path('signin/', SigninView.as_view(), name='signin'),
# ]
