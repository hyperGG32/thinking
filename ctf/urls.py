from django.urls import path

from . import views

app_name = "ctf"

urlpatterns = [
    path("challenges/", views.ChallengeList.as_view(), name="challenges"),
    path("challenges/<int:pk>/", views.ChallengeDetail.as_view(), name="ind_challenge"),
    path("categories/", views.CategoryList.as_view(), name="categories"),
    path("categories/<int:pk>/", views.CategoryDetail.as_view(), name="ind_category"),
]
