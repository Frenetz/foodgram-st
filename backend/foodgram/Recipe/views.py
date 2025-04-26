from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
# from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import Recipe, RecipeIngredient, Favorite, ShoppingCart
from .serializers import RecipeCreateSerializer, RecipeReadSerializer
from .serializers import RecipeShortSerializer
from rest_framework.pagination import PageNumberPagination
from collections import defaultdict


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 5
    max_page_size = 100


@api_view(['GET', 'POST'])
def recipes_list(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется авторизация.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = RecipeCreateSerializer(data=request.data,
                                            context={'request': request})
        if serializer.is_valid():
            recipe = serializer.save()
            read_serializer = RecipeReadSerializer(
                recipe,
                context={'request': request}
            )
            return Response(
                read_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    recipes = Recipe.objects.all()
    author = request.query_params.get('author')
    is_favorited = request.query_params.get('is_favorited')
    is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')

    if author:
        recipes = recipes.filter(author__id=author)

    if request.user.is_authenticated:
        if is_favorited == '1':
            recipes = recipes.filter(favorites__user=request.user)
        if is_in_shopping_cart == '1':
            recipes = recipes.filter(shopping_cart__user=request.user)
    recipes = recipes.order_by('-created_at')
    paginator = CustomPagination()
    result_page = paginator.paginate_queryset(recipes, request)
    serializer = RecipeReadSerializer(
        result_page,
        many=True,
        context={'request': request}
    )
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PATCH', 'DELETE'])
def get_recipe_detail(request, id):
    try:
        recipe = Recipe.objects.get(pk=id)
    except Recipe.DoesNotExist:
        return Response(
            {'detail': 'Страница не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = RecipeReadSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'PATCH':
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if recipe.author != request.user:
            return Response(
                {'detail': 'У вас недостаточно прав для выполнения '
                 'данного действия.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RecipeCreateSerializer(
            recipe,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            RecipeIngredient.objects.filter(recipe=recipe).delete()
            serializer.save()
            response_serializer = RecipeReadSerializer(
                recipe,
                context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if recipe.author != request.user:
            return Response(
                {'detail': 'У вас недостаточно прав для выполнения '
                 'данного действия.'},
                status=status.HTTP_403_FORBIDDEN
            )

        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_recipe_short_link(request, id):
    try:
        recipe = Recipe.objects.get(pk=id)
    except Recipe.DoesNotExist:
        return Response(
            {'detail': 'Страница не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )
    short_link = generate_short_link(recipe)
    return Response({'short-link': short_link}, status=status.HTTP_200_OK)


def generate_short_link(recipe):
    base_url = 'http://localhost/recipes/'
    short_link = f'{base_url}{recipe.id}/'
    return short_link


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def favorite_recipe_view(request, id):
    try:
        recipe = Recipe.objects.get(pk=id)
    except Recipe.DoesNotExist:
        return Response(
            {'detail': 'Страница не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'POST':
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {"detail": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Favorite.objects.create(user=request.user, recipe=recipe)

        data = {
            "id": recipe.id,
            "name": recipe.name,
            "image": request.build_absolute_uri(recipe.image.url),
            "cooking_time": recipe.cooking_time,
        }
        return Response(data, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        favorite = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).first()
        if not favorite:
            return Response(
                {"detail": "Рецепт не найден в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    user = request.user
    shopping_cart_recipes = ShoppingCart.objects.filter(user=user).values_list(
        'recipe',
        flat=True
    )

    if not shopping_cart_recipes:
        return HttpResponse("Список покупок пуст.", content_type='text/plain')

    ingredients_summary = defaultdict(float)

    recipe_ingredients = RecipeIngredient.objects.filter(
        recipe__in=shopping_cart_recipes
    )

    for ri in recipe_ingredients:
        name = f"{ri.ingredient.name} ({ri.ingredient.measurement_unit})"
        ingredients_summary[name] += ri.amount

    lines = ["Шопинг лист:\n"]
    lines += [
        f"- {name} — "
        f"{int(amount) if amount.is_integer() else round(amount, 2)}"
        for name, amount in ingredients_summary.items()
    ]
    content = "\n".join(lines)

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_cart.txt"'
    )
    return response


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def shopping_cart(request, id):
    user = request.user
    try:
        recipe = Recipe.objects.get(pk=id)
    except Recipe.DoesNotExist:
        return Response(
            {"detail": "Рецепт не найден."},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'POST':
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"detail": "Рецепт уже в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        try:
            item = ShoppingCart.objects.get(user=user, recipe=recipe)
        except ShoppingCart.DoesNotExist:
            return Response(
                {"detail": "Рецепта не было в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
