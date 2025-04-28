from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Recipe, RecipeIngredient, Favorite, Ingredient


class IngredientHasRecipesFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(ingredient_recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(ingredient_recipes__isnull=True).distinct()
        return queryset


class CookingTimeCategoryFilter(admin.SimpleListFilter):
    title = 'Категория времени готовки'
    parameter_name = 'cooking_time_cat'

    def lookups(self, request, model_admin):
        return (
            ('fast', 'Быстро (< 15 мин)'),
            ('medium', 'Средне (15-30 мин)'),
            ('long', 'Долго (> 30 мин)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lte=15)
        if self.value() == 'medium':
            return queryset.filter(cooking_time__gt=15, cooking_time__lte=30)
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=30)
        return queryset


class UserHasRecipesFilter(admin.SimpleListFilter):
    title = 'Есть рецепты'
    parameter_name = 'user_has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True).distinct()
        return queryset


class UserHasSubscriptionsFilter(admin.SimpleListFilter):
    title = 'Есть подписки'
    parameter_name = 'user_has_subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscriptions__isnull=True).distinct()
        return queryset


class UserHasSubscribersFilter(admin.SimpleListFilter):
    title = 'Есть подписчики'
    parameter_name = 'user_has_subscribers'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscribers__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscribers__isnull=True).distinct()
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительно', {'fields': ('first_name', 'last_name', 'avatar')}),
    )

    search_fields = ('email', 'username', 'first_name', 'last_name')

    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_display',
        'recipe_count',
        'subscription_count',
        'subscriber_count',
        'is_active'
    )

    list_filter = (
        'is_active',
        UserHasRecipesFilter,
        UserHasSubscriptionsFilter,
        UserHasSubscribersFilter,
    )

    readonly_fields = (
        'avatar_display',
        'recipe_count',
        'subscription_count',
        'subscriber_count'
    )

    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip() or '-'
    full_name.short_description = 'ФИО'

    def avatar_display(self, user):
        if user.avatar:
            return format_html(
                '<img src="{}" width="30" height="30" '
                'style="border-radius: 50%;" />',
                user.avatar.url
            )
        return '–'
    avatar_display.short_description = 'Аватар'

    def recipe_count(self, user):
        return user.recipes.count()
    recipe_count.short_description = 'Рецепты'

    def subscription_count(self, user):
        return user.subscriptions.count()
    subscription_count.short_description = 'Подписки'

    def subscriber_count(self, user):
        return user.subscribers.count()
    subscriber_count.short_description = 'Подписчики'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = (
        'id',
        'name',
        'author',
        'display_image',
        'display_ingredients_short',
        'cooking_time',
        'get_favorites_count',
        'created_at',
    )
    readonly_fields = ('get_favorites_count', 'display_image')

    search_fields = ('name', 'author__username', 'ingredients__name')
    list_filter = ('author', CookingTimeCategoryFilter, 'ingredients')

    autocomplete_fields = ('author',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related(
            'ingredients', 'recipe_favorites'
        )

    def get_favorites_count(self, recipe):
        return Favorite.objects.filter(recipe=recipe).count()
    get_favorites_count.short_description = 'В избранном'

    def display_ingredients_short(self, recipe):
        ingredients = recipe.ingredients.all()[:3]
        names = [ing.name for ing in ingredients]
        if recipe.ingredients.count() > 3:
            names.append('...')
        return ', '.join(names) or '-'
    display_ingredients_short.short_description = 'Ингредиенты (кратко)'

    def display_image(self, recipe):
        if recipe.image:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="object-fit: cover;" />',
                recipe.image.url
            )
        return '–'
    display_image.short_description = 'Картинка'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipe_count_display')
    search_fields = ('name',)
    list_filter = ('measurement_unit', IngredientHasRecipesFilter)

    def recipe_count_display(self, ingredient):
        return ingredient.ingredient_recipes.count()
    recipe_count_display.short_description = 'Используется в рецептах'
