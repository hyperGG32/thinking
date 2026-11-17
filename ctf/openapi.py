from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from rest_framework import serializers

from .models import Challenge
from .serializers import ChallengeListSerializer


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    fields = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), allow_null=True
    )


class PaginatedChallengeListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ChallengeListSerializer(many=True)


def error(description):
    return OpenApiResponse(ErrorSerializer, description=description)


CHALLENGE_FILTERS = [
    OpenApiParameter("search", str, description="Пошук у назві задачі"),
    OpenApiParameter("category", int, description="id категорії"),
    OpenApiParameter("author", int, description="id автора"),
    OpenApiParameter("difficulty", str, enum=Challenge.Difficulty.values),
    OpenApiParameter("status", str, enum=Challenge.Status.values,
                     description="Фільтрує лише в межах задач, які видно користувачу"),
    OpenApiParameter("ordering", str, default="-created_at",
                     enum=["points", "-points", "created_at", "-created_at",
                           "solves", "-solves"]),
    OpenApiParameter("page", int, description="Номер сторінки, по 20 задач")
]
