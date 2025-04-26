from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_list),
    path('auth/token/login/', views.authenticate_user),
    path('auth/token/logout/', views.logout_view),
    path('users/set_password/', views.set_password),
    path('users/me/avatar/', views.set_avatar),
    path('users/<int:id>/', views.user_profile),
    path('users/me/', views.get_current_user),
    path('users/subscriptions/', views.get_user_subscriptions),
    path('users/<int:id>/subscribe/', views.manage_subscription)
]
