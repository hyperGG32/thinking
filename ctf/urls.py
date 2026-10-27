from django.urls import path

from . import views

app_name = "ctf"

urlpatterns = [
    path("challenges/", views.ChallengeList.as_view()),
    path("challenges/<int:pk>/", views.ChallengeDetail.as_view()),
    path("categories/", views.CategoryList.as_view()),
    path("categories/<int:pk>/", views.CategoryDetail.as_view()),
]
