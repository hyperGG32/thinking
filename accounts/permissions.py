from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    message = "Змінювати може лише автор задачі або адміністратор"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    message = "Змінювати може лише адміністратор"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff
