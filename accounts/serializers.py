from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, write_only=True)
    password_conf = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "password",
                  "password_conf"]

    def validate_username(self, username):
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Користувач з таким ім'ям вже існує")
        return username

    def validate_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Користувач з такою поштою вже існує")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_conf"]:
            raise serializers.ValidationError({"password_conf": "Паролі не "
                                               "збігаються"})

        user = User(
            email=attrs["email"],
            username=attrs["username"],
            first_name=attrs.get("first_name"),
            last_name=attrs.get("last_name"),
        )
        try:
            password_validation.validate_password(attrs["password"], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_conf")
        return User.objects.create_user(**validated_data)

