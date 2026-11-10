from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly

from .exceptions import Conflict
from .models import Category, Challenge
from .serializers import (
    CategorySerializer,
    ChallengeDetailSerializer,
    ChallengeListSerializer,
)

ORDERING = {"points", "-points", "created_at", "-created_at", "solves", "-solves"}
TRANSITIONS = {
    "draft": {"review"},
    "review": {"rejected", "active"},
    "active": set(),
    "rejected": {"review"},
}


class ChallengeList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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

    def post(self, request):
        serializer = ChallengeDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChallengeDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)
        if (
            challenge.status != "active"
            and not request.user.is_staff
            and request.user != challenge.author
        ):
            raise NotFound()
        return Response(ChallengeDetailSerializer(challenge).data)

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
