from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from .serializers import UserTokenSerializer

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view()),
    path("token/", TokenObtainPairView.as_view(serializer_class=UserTokenSerializer),
         name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", views.MeView.as_view(), name="me")
]
