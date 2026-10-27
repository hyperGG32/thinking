from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .models import Challenge, Category
from .serializers import (ChallengeDetailSerializer, ChallengeListSerializer,
                          CategorySerializer)

ORDERING = {"points", "-points", "created_at", "-created_at"}


class ChallengeList(APIView):
    def get(self, request):
        challenges = Challenge.objects.all()
        return Response(ChallengeListSerializer(challenges, many=True).data)

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
