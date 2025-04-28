from django.core.management.base import BaseCommand
from recipes.models import Ingredient
import json
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Загружает данные ингредиентов из файла JSON'

    def handle(self, *args, **kwargs):
        try:
            if settings.DEBUG:
                json_file_path = os.path.join(
                    settings.BASE_DIR, '../../data/ingredients.json'
                )
            else:
                json_file_path = os.path.join(
                    settings.BASE_DIR, 'data/ingredients.json'
                )

            with open(json_file_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)

            ingredients_to_create = [
                Ingredient(**ingredient_data)
                for ingredient_data in ingredients_data
            ]

            Ingredient.objects.bulk_create(ingredients_to_create)

            self.stdout.write(self.style.SUCCESS(
                f'{len(ingredients_to_create)} ингредиентов успешно загружено!'
            )
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Произошла ошибка: {e}'))
