from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('User.urls')),
    path('api/', include('Ingredient.urls')),
    path('api/', include('Recipe.urls'))
    # path('api/recipes/', include('Recipe.urls')),
    # path('api/ingredients/', include('Ingradient.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
