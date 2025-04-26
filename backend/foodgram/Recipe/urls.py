from django.urls import path
from . import views

urlpatterns = [
    path('recipes/', views.recipes_list),
    path('recipes/<int:id>/', views.get_recipe_detail),
    path('recipes/<int:id>/get-link/', views.get_recipe_short_link),
    path('recipes/<int:id>/favorite/', views.favorite_recipe_view),
    path('recipes/download_shopping_cart/', views.download_shopping_cart),
    path('recipes/<int:id>/shopping_cart/', views.shopping_cart)
]
