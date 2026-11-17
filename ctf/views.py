from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly

from drf_spectacular.utils import OpenApiExample, extend_schema

from .exceptions import Conflict
from .models import Category, Challenge
from .serializers import (
    CategorySerializer,
    ChallengeDetailSerializer,
    ChallengeListSerializer,
)
from .openapi import CHALLENGE_FILTERS, PaginatedChallengeListSerializer, error

ORDERING = {"points", "-points", "created_at", "-created_at", "solves", "-solves"}
TRANSITIONS = {
    "draft": {"review"},
    "review": {"rejected", "active"},
    "active": set(),
    "rejected": {"review"},
}


class ChallengeList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["challenges"],
        summary="Список задач",
        operation_id="challenges_list",
        description="Анонім бачить active; користувач - active і свої; адмін - усі.",
        parameters=CHALLENGE_FILTERS,
        responses={
            200: PaginatedChallengeListSerializer,
            400: error("Невалідний фільтр"),
            404: error("Сторінки не існує")
        },
    )
    def get(self, request):
        challenges = Challenge.objects.all()
        params = request.query_params
        search = params.get("search")
        category = params.get("category")
        author = params.get("author")
        difficulty = params.get("difficulty")
        status_ = params.get("status")
        ordering = params.get("ordering", "-created_at")

        if not request.user.is_staff:
            if request.user.is_authenticated:
                challenges = challenges.filter(
                    Q(status="active") | Q(author=request.user)
                )
            else:
                challenges = challenges.filter(status="active")

        if search:
            challenges = challenges.filter(title__icontains=search)
        if category:
            if not category.isdigit():
                raise ValidationError({"category": ["Має бути цілим числом!"]})
            challenges = challenges.filter(category_id=category)
        if author:
            if not author.isdigit():
                raise ValidationError({"author": ["Має бути цілим числом!"]})
            challenges = challenges.filter(author_id=author)

        if difficulty:
            if difficulty not in Challenge.Difficulty.values:
                raise ValidationError(
                    {
                        "difficulty": [
                            f"Дозволено: {', '.join(Challenge.Difficulty.values)}"
                        ]
                    }
                )
            challenges = challenges.filter(difficulty=difficulty)

        if status_:
            if status_ not in Challenge.Status.values:
                raise ValidationError(
                    {"status": [f"Дозволено: {', '.join(Challenge.Status.values)}"]}
                )
            challenges = challenges.filter(status=status_)

        if ordering not in ORDERING:
            raise ValidationError(
                {"ordering": [f"Дозволено: {', '.join(sorted(ORDERING))}"]}
            )
        if ordering in ("solves", "-solves"):  # solves поки завжди 0
            ordering = "-created_at"
        challenges = challenges.order_by(ordering, "-id")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(challenges, request, view=self)
        return paginator.get_paginated_response(
            ChallengeListSerializer(page, many=True).data
        )

    @extend_schema(
        tags=["challenges"],
        summary="Створити задачу",
        description="Задача завжди створюється як draft; автор - поточний користувач.",
        request=ChallengeDetailSerializer,
        responses={
            201: ChallengeDetailSerializer,
            400: error("Невалідні поля"),
            401: error("Без токена"),
        },
        examples=[
            OpenApiExample(
                "Нова задача",
                request_only=True,
                value={
                    "title": "Baby RSA",
                    "description": "Розклади n на множники",
                    "category": 1,
                    "difficulty": "easy",
                    "points": 100,
                    "flag": "CTF{small_primes}",
                    "connection_info": "nc ctf.local 1337",
                },
            )
        ],
    )
    def post(self, request):
        serializer = ChallengeDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChallengeDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    @extend_schema(
        tags=["challenges"],
        summary="Одна задача",
        responses={
            200: ChallengeDetailSerializer,
            404: error("Не існує або не active, а ви не автор і не адмін"),
        },
    )
    def get(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)
        if (
            challenge.status != "active"
            and not request.user.is_staff
            and request.user != challenge.author
        ):
            raise NotFound()
        return Response(ChallengeDetailSerializer(challenge).data)

    @extend_schema(
        tags=["challenges"],
        summary="Редагувати задачу або змінити статус",
        request=ChallengeDetailSerializer,
        responses={
            200: ChallengeDetailSerializer,
            400: error("Невалідні поля або неіснуючий статус"),
            401: error("Без токена"),
            403: error("Не автор і не адмін; або не адмін ставить active/rejected"),
            404: error("Задача не існує"),
            409: error("Недозволений перехід статусу"),
        },
        examples=[OpenApiExample("На модерацію", request_only=True,
                                 value={"status": "review"})],
    )
    def patch(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)

        self.check_object_permissions(request, challenge)

        new_status = request.data.get("status")

        if new_status is not None:
            if new_status not in Challenge.Status.values:
                raise ValidationError(
                    {"status": [f"Дозволені: {', '.join(Challenge.Status.values)}"]}
                )
            allowed = TRANSITIONS[challenge.status]
            if new_status in {"active", "rejected"} and not request.user.is_staff:
                raise PermissionDenied(
                    "Публікувати чи відхиляти задачі може тільки "
                    "адміністратор. Надішліть задачу на рев'ю"
                )
            if new_status not in allowed:
                raise Conflict(
                    f"Опа! Неможливо перейти з {challenge.status} на "
                    f"{new_status}. Дозволені: "
                    f"{
                        ', '.join(sorted(allowed))
                        or 'жодного. Тобто, неможливо змінити статус!'
                    }"
                )

        serializer = ChallengeDetailSerializer(
            challenge, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        if new_status is not None:
            serializer.save(status=new_status)
        else:
            serializer.save()
        return Response(serializer.data)

    @extend_schema(
        tags=["challenges"],
        summary="Видалити задачу",
        responses={
            204: None,
            401: error("Без токена"),
            403: error("Не автор і не адмін"),
            404: error("Задача не існує"),
        },
    )
    def delete(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)
        self.check_object_permissions(request, challenge)
        challenge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryList(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        category = Category.objects.all()
        return Response(CategorySerializer(category, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetail(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk):
        category = get_object_or_404(Category, id=pk)
        return Response(CategorySerializer(category).data)

    def patch(self, request, pk):
        category = get_object_or_404(Category, id=pk)
        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        category = get_object_or_404(Category, id=pk)
        count = category.challenges.count()
        if count:
            raise Conflict(
                f"Отакої! Не можемо видалити {category.name}, поки у ній є"
                f" завдання. Зараз їх {count}! Спершу видаліть або "
                f"перенесіть, і спробуйте ще раз!"
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
