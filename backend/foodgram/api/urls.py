from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import user_views, recipe_views, ingredient_views

router = DefaultRouter()

router.register(r'users', user_views.UserViewSet, basename='users')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]

other_router = DefaultRouter()
other_router.register(
    r'recipes',
    recipe_views.RecipeViewSet,
    basename='recipes'
)
other_router.register(
    r'ingredients',
    ingredient_views.IngredientViewSet,
    basename='ingredients'
)
urlpatterns += [path('', include(other_router.urls))]
