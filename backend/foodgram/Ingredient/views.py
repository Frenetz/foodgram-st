# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Ingredient
from .serializers import IngredientSerializer


@api_view(['GET'])
def ingredient_list(request):
    name = request.query_params.get('name')
    if name:
        ingredients = Ingredient.objects.filter(name__istartswith=name)
    else:
        ingredients = Ingredient.objects.all()
    serializer = IngredientSerializer(ingredients, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def ingredient_detail(request, id):
    try:
        ingredient = Ingredient.objects.get(id=id)
    except Ingredient.DoesNotExist:
        return Response({'detail': 'Ингредиент не найден'},
                        status=status.HTTP_404_NOT_FOUND)
    serializer = IngredientSerializer(ingredient)
    return Response(serializer.data)
