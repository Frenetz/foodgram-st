from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from collections import defaultdict
from datetime import datetime
from django.http import FileResponse
import io
from recipes.models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    User
)
from ..serializers.recipe_serializers import (
    RecipeCreateSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeUpdateSerializer
)
from rest_framework.pagination import PageNumberPagination
import django_filters
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    BooleanFilter
)
from rest_framework import filters


class RecipePagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6
    max_page_size = 100


class RecipeFilter(FilterSet):
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'recipe_ingredients__ingredient', 'favorites', 'shopping_cart'
    ).order_by('-created_at')
    pagination_class = RecipePagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ('name',)

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        if self.action == 'partial_update':
            return RecipeUpdateSerializer
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in [
            'create',
            'partial_update',
            'destroy',
            'favorite',
            'shopping_cart',
            'download_shopping_cart'
        ]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(author=self.request.user)
        read_serializer = RecipeReadSerializer(
            instance,
            context=self.get_serializer_context()
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.author != request.user:
            return Response(
                {
                    'detail': (
                        'У вас недостаточно прав для выполнения '
                        'данного действия.'
                    ),
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        read_serializer = RecipeReadSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {
                    'detail': (
                        'У вас недостаточно прав для выполнения '
                        'данного действия.'
                    ),
                },
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def short_link(self, request, pk=None):
        instance = self.get_object()
        url = (
            f"{request.scheme}://{request.get_host()}"
            f"/short-link/{instance.id}"
        )
        return Response({"short-link": url}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        favorite_exists = Favorite.objects.filter(
            user=user, recipe=recipe
        ).exists()

        if request.method == 'POST':
            if favorite_exists:
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not favorite_exists:
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        cart_item_exists = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).exists()

        if request.method == 'POST':
            if cart_item_exists:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not cart_item_exists:
            return Response(
                {'errors': 'Рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = (
            ShoppingCart.objects
            .filter(user=user)
            .select_related('recipe')
        )

        if not shopping_cart_items.exists():
            return Response(
                {'errors': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients_summary = defaultdict(
            lambda: {'amount': 0, 'unit': '', 'recipes': set()}
        )
        recipe_ids = [item.recipe.id for item in shopping_cart_items]
        recipe_ingredients = RecipeIngredient.objects.filter(
            recipe__id__in=recipe_ids
        ).select_related('ingredient', 'recipe__author')

        for ri in recipe_ingredients:
            name = ri.ingredient.name.capitalize()
            unit = ri.ingredient.measurement_unit
            amount = ri.amount
            author_name = (
                ri.recipe.author.get_full_name()
                or ri.recipe.author.username
            )
            author_info = f"(автор: {author_name})"

            recipe_info = (
                f"{ri.recipe.name} {author_info}"
            )

            ingredients_summary[name]['amount'] += amount
            ingredients_summary[name]['unit'] = unit
            ingredients_summary[name]['recipes'].add(recipe_info)

        lines = [
            (
                f"Список покупок для пользователя: "
                f"{user.get_full_name() or user.username}"
            ),
            f"Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
        ]
        for idx, (name, data) in enumerate(
            sorted(ingredients_summary.items()),
            1
        ):
            amount = (
                int(data['amount'])
                if data['amount'] == int(data['amount'])
                else data['amount']
            )
            recipes_list = ', '.join(sorted(data['recipes']))
            lines.append(f"{idx}. {name} ({data['unit']}) — {amount}")
            lines.append(f"    Используется в: {recipes_list}\n")

        content = "\n".join(lines)

        file_buffer = io.BytesIO()
        file_buffer.write(content.encode('utf-8'))
        file_buffer.seek(0)

        filename = 'shopping_cart.txt'
        response = FileResponse(
            file_buffer, as_attachment=True, filename=filename
        )
        response['Content-Type'] = 'text/plain; charset=utf-8'
        return response
