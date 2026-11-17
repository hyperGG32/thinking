from django.contrib import admin

from .models import Category, Challenge


class ChallengeAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "difficulty", "status", "points"]


admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(Category)
