import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from recipes.models import Recipe, RecipeIngredient, Ingredient, \
    User, Favorite, ShoppingCart
from djoser.serializers import UserSerializer as DjoserUserSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                name = f"{uuid.uuid4()}.{ext}"
                data = ContentFile(base64.b64decode(imgstr), name=name)
            except Exception:
                raise serializers.ValidationError(
                    "Ошибка обработки изображения."
                )
        return super().to_internal_value(data)


class AuthorSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')
        read_only_fields = (
            DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')
        )

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        if user.is_authenticated and user != author:
            return user.subscriptions.filter(author=author).exists()
        return False


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()
    author = AuthorSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'name', 'text',
            'cooking_time', 'image', 'ingredients'
        ]
        read_only_fields = ('id', 'author')

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо добавить хотя бы один ингредиент.'}
            )
        ingredient_ids = []
        for item in ingredients:
            if item['id'] in ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться.'}
                )
            ingredient_ids.append(item['id'])
        return ingredients

    def _create_or_update_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._create_or_update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.get('ingredients', [])
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо добавить хотя бы один ингредиент.'}
            )
        if 'ingredients' in validated_data:
            validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        self._create_or_update_ingredients(instance, ingredients_data)
        instance.refresh_from_db()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeUpdateSerializer(RecipeCreateSerializer):
    image = Base64ImageField(required=False)

    class Meta(RecipeCreateSerializer.Meta):
        pass


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]
        read_only_fields = fields

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).exists()
        return False

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists()
        return False


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
