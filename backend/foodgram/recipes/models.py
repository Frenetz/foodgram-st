from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(
            1, 'Время приготовления должно быть не меньше 1')
        ]
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор публикации'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1, 'Количество должно быть не меньше 1')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        unique_together = ['recipe', 'ingredient']
        ordering = ['id']

    def __str__(self):
        return f'{self.ingredient.name} — {int(self.amount)}' \
               f'{self.ingredient.measurement_unit} в {self.recipe.name}'


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ['user', 'recipe']

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        unique_together = ['user', 'recipe']

    def __str__(self):
        return f'{self.user} добавил в список покупок {self.recipe}'


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Адрес электронной почты"
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(r'^[\w.@+-]+\Z', 'Enter a valid username.')
        ],
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

    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Автор, на которого подписаны'
    )
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('subscriber')),
                name='prevent_self_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['id']

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
