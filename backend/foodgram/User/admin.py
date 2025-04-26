from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User

    search_fields = ('email', 'username')

    list_display = ('email', 'username', 'first_name',
                    'last_name', 'is_active')
