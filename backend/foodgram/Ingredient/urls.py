from django.urls import path
from . import views

urlpatterns = [
    path('ingredients/', views.ingredient_list, name='ingredient-list'),
    path('ingredients/<int:id>/',
         views.ingredient_detail,
         name='ingredient-detail'),
]
