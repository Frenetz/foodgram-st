from django.core.management.base import BaseCommand
from Ingredient.models import Ingredient
import json
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Загружает данные ингредиентов из файла JSON'

    def handle(self, *args, **kwargs):
        if settings.DEBUG:
            json_file_path = os.path.join(settings.BASE_DIR,
                                          '../../data/ingredients.json')
        else:
            json_file_path = os.path.join(settings.BASE_DIR,
                                          'data/ingredients.json')

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for ingredient_data in data:
            ingredient = Ingredient(
                name=ingredient_data['name'],
                measurement_unit=ingredient_data['measurement_unit']
            )
            ingredient.save()
        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены!'))
