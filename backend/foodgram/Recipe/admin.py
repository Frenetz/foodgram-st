from django.contrib import admin
from .models import Recipe, Favorite

# Register your models here.


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorites_count')

    search_fields = ('name', 'author__username')

    def get_favorites_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    get_favorites_count.short_description = 'Количество добавлений в избранное'
