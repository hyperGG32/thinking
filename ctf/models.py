from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва", unique=True)

    def __str__(self):
        return self.name


class Challenge(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Легкий'
        MEDIUM = 'medium', 'Середній'
        HARD = 'hard', 'Важкий'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Чернетка'
        REVIEW = 'review', 'У перегляді'
        ACTIVE = 'active', 'Активний'
        REJECTED = 'rejected', 'Відмовлено'

    title = models.CharField(max_length=256, verbose_name="Назва")
    description = models.TextField(verbose_name="Опис")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="challenges",
        verbose_name="Категорія"
    )
    difficulty = models.CharField(verbose_name="Складність", choices=Difficulty,
                                  max_length=10)
    points = models.PositiveIntegerField(verbose_name="Очки")
    flag = models.CharField(verbose_name="Хеш прапору", max_length=64)  # stored in hex
    connection_info = models.CharField(verbose_name="Сокет сервера", default='',
                                       blank=True, max_length=512)
    status = models.CharField(verbose_name="Статус", choices=Status,
                              default=Status.DRAFT, max_length=10)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True,
                               blank=True)
    created_at = models.DateTimeField(verbose_name="Дата Створення", auto_now_add=True)

    def __str__(self):
        return self.title

