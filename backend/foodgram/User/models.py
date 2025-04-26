from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        validators=[EmailValidator()],
        verbose_name="Адрес электронной почты"
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+\Z',
                                   'Enter a valid username.')],
        verbose_name="Уникальный юзернейм"
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя"
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия"
    )

    password = models.CharField(
        max_length=128,
        verbose_name="Пароль"
    )

    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    def __str__(self):
        return self.username

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Пользователь, на которого подписаны'
    )
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Пользователь, который подписан'
    )

    class Meta:
        unique_together = ('author', 'subscriber')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
