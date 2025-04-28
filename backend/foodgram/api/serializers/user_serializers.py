from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from recipes.models import User, Subscription
from .recipe_serializers import RecipeShortSerializer


class UserGetSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_avatar(self, user):
        request = self.context.get('request')
        if user.avatar and hasattr(user.avatar, 'url') and request:
            return request.build_absolute_uri(user.avatar.url)
        return None

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        current_user = request.user if request else None

        if (
            not current_user
            or not current_user.is_authenticated
            or current_user == user
        ):
            return False

        return Subscription.objects.filter(
            author=user,
            subscriber=current_user
        ).exists()


class SubscriptionUserSerializer(UserGetSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(UserGetSerializer.Meta):
        fields = (
            UserGetSerializer.Meta.fields
            + ('recipes', 'recipes_count')
        )
        read_only_fields = (
            UserGetSerializer.Meta.read_only_fields
            + ('recipes', 'recipes_count')
        )

    def get_recipes(self, user):
        request = self.context.get('request')
        recipes_limit = 5
        if request and hasattr(request, 'query_params'):
            recipes_limit_str = request.query_params.get('recipes_limit', '5')
            try:
                limit = int(recipes_limit_str)
                if limit > 0:
                    recipes_limit = limit
            except (ValueError, TypeError):
                pass

        recipes = user.recipes.all()[:recipes_limit]
        return RecipeShortSerializer(
            recipes, many=True,
            context=self.context
        ).data

    def get_recipes_count(self, user):
        return user.recipes.count()


class UserRegisterSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
