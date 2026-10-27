from rest_framework import serializers
from .models import Challenge, Category
from hashlib import sha256


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class CategoryField(serializers.PrimaryKeyRelatedField):
    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        return CategorySerializer(value).data


class AuthorField(serializers.Serializer):
    id = serializers.IntegerField()
    nickname = serializers.CharField(source="username")


class ChallengeListSerializer(serializers.ModelSerializer):
    category = CategoryField(queryset=Category.objects.all())
    author = AuthorField(read_only=True)
    solves = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ["id", "title", "difficulty", "points", "category", "author", "solves"]

    def get_solves(self, obj):
        return 0


class ChallengeDetailSerializer(ChallengeListSerializer):
    flag = serializers.CharField(write_only=True)
    first_blood = serializers.SerializerMethodField()

    class Meta(ChallengeListSerializer.Meta):
        fields = ChallengeListSerializer.Meta.fields + [
            "description", "connection_info", "status", "flag", "first_blood",
            "created_at"
        ]
        read_only_fields = ["status", "created_at"]

    def validate_flag(self, flag):
        return sha256(flag.encode()).hexdigest()

    def get_first_blood(self, obj):
        return None
    