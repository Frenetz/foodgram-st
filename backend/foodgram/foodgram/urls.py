from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views.recipe_views import RecipeViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('short-link/<int:pk>/', RecipeViewSet.as_view({"get": "retrieve"}))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
