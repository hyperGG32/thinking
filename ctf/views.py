from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .models import Challenge, Category
from .serializers import (ChallengeDetailSerializer, ChallengeListSerializer,
                          CategorySerializer)

ORDERING = {"points", "-points", "created_at", "-created_at", "solves", "-solves"}


class ChallengeList(APIView):
    def get(self, request):
        challenges = Challenge.objects.all()
        params = request.query_params
        search = params.get("search")
        category = params.get("category")
        author = params.get("author")
        difficulty = params.get("difficulty")
        status_ = params.get("status")
        ordering = params.get("ordering", "-created_at")

        if search:
            challenges = challenges.filter(title__icontains=search)
        if category:
            if not category.isdigit():
                raise ValidationError({"category": ["Має бути цілим числом"]})
            challenges = challenges.filter(category_id=category)
        if author:
            if not author.isdigit():
                raise ValidationError({"author": ["Має бути цілим числом"]})
            challenges = challenges.filter(author_id=author)

        if difficulty:
            if difficulty not in Challenge.Difficulty.values:
                raise ValidationError({"difficulty": [
                    f"Дозволено: {', '.join(Challenge.Difficulty.values)}"]})
            challenges = challenges.filter(difficulty=difficulty)

        if status_:
            if status_ not in Challenge.Status.values:
                raise ValidationError(
                    {"status": [f"Дозволено: {', '.join(Challenge.Status.values)}"]})
            challenges = challenges.filter(status=status_)

        if ordering not in ORDERING:
            raise ValidationError(
                {"ordering": [f"Дозволено: {', '.join(sorted(ORDERING))}"]})
        if ordering in ("solves", "-solves"):  # solves поки завжди 0
            ordering = "-created_at"
        challenges = challenges.order_by(ordering, "-id")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(challenges, request, view=self)
        return paginator.get_paginated_response(
            ChallengeListSerializer(page, many=True).data)

    def post(self, request):
        serializer = ChallengeDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChallengeDetail(APIView):
    def get(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)
        return Response(ChallengeDetailSerializer(challenge).data)

    def patch(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)
        serializer = ChallengeDetailSerializer(challenge, data=request.data,
                                               partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        challenge = get_object_or_404(Challenge, id=pk)
        challenge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryList(APIView):
    def get(self, request):
        category = Category.objects.all()
        return Response(CategorySerializer(category, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetail(APIView):
    def get(self, request, pk):
        category = get_object_or_404(Category, id=pk)
        return Response(CategorySerializer(category).data)

    def patch(self, request, pk):
        category = get_object_or_404(Category, id=pk)
        serializer = CategorySerializer(category, data=request.data, partial=True, )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        category = get_object_or_404(Category, id=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


