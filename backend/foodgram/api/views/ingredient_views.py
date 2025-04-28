from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from ..serializers.ingredient_serializers import IngredientSerializer
from recipes.models import Ingredient
from rest_framework.exceptions import MethodNotAllowed


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name', None)
        if name:
            return Ingredient.objects.filter(name__istartswith=name)
        return Ingredient.objects.all()

    def retrieve(self, request, pk=None):
        try:
            ingredient = Ingredient.objects.get(id=pk)
        except Ingredient.DoesNotExist:
            return Response({'detail': 'Ингредиент не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(ingredient)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="Метод не разрешён")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="Метод не разрешён")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH", detail="Метод не разрешён")

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="Метод не разрешён")
