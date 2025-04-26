from django.contrib import admin
from .models import Ingredient

# Register your models here.


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')

    search_fields = ('name',)
