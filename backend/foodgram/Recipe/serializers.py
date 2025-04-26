from rest_framework import serializers
from .models import Recipe, RecipeIngredient
from Ingredient.models import Ingredient
import base64
import uuid
from django.core.files.base import ContentFile
from User.models import User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=name)
        return super().to_internal_value(data)


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.FloatField()

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError("Количество должно быть "
                                              "положительным.")
        return data


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['name', 'text', 'cooking_time', 'image', 'ingredients']

    def validate(self, data):
        ingredients = data.get('ingredients')
        cooking_time = data.get('cooking_time')

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Необходимо добавить хотя бы один ингредиент.'
            })

        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно '
                'быть не меньше 1 минуты.'
            })

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)

        self._create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)

        if 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()

        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self._create_ingredients(instance, ingredients_data)

        return instance

    def _create_ingredients(self, recipe, ingredients_data):
        ingredient_ids = [item['id'] for item in ingredients_data]
        ingredients = Ingredient.objects.filter(id__in=ingredient_ids)
        ingredients_map = {
            ingredient.id: ingredient
            for ingredient in ingredients
        }

        for item in ingredients_data:
            ingredient = ingredients_map.get(item['id'])
            if not ingredient:
                raise serializers.ValidationError({
                    'ingredients': f"Ингредиент с id {item['id']} не найден."
                })
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=item['amount']
            )


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.subscriptions.filter(author=obj).exists()
        return False


class RecipeListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'author', 'image', 'text',
                  'cooking_time', 'ingredients']

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.FloatField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeReadSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.shopping_cart.filter(user=user).exists()
        return False


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
