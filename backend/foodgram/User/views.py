from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from .models import User, Subscription
from .serializers import UserGetSerializer, UserRegisterSerializer
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.password_validation import validate_password
import base64
import uuid
import imghdr
from django.core.files.base import ContentFile
from Recipe.models import Recipe
from Recipe.serializers import RecipeShortSerializer


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 5
    max_page_size = 100


@api_view(['GET', 'POST'])
def user_list(request):
    if request.method == 'POST':
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        paginator = CustomPagination()
        users = User.objects.all()
        result_page = paginator.paginate_queryset(users, request)
        serializer = UserGetSerializer(
            result_page,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
def authenticate_user(request):
    email = request.data.get('email')
    password = request.data.get('password')
    if not email or not password:
        return Response({'detail': 'Email и пароль обязательны'},
                        status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, username=email, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})
    else:
        return Response({'detail': 'Неверный email или пароль'},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    user = request.user
    new_password = request.data.get('new_password')
    current_password = request.data.get('current_password')
    if not new_password:
        return Response({'new_password': 'Это поле обязательно.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if current_password and not user.check_password(current_password):
        return Response({'current_password': 'Неверный текущий пароль.'},
                        status=status.HTTP_400_BAD_REQUEST)
    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def set_avatar(request):
    user = request.user

    if request.method == 'PUT':
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response({'avatar': 'Это поле обязательно.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            if "base64," in avatar_data:
                avatar_data = avatar_data.split("base64,")[1]
            decoded_image = base64.b64decode(avatar_data)
            image_type = imghdr.what(None, decoded_image)
            if image_type not in ['jpeg', 'png', 'gif']:
                return Response({'avatar': 'Неверный формат изображения.'},
                                status=status.HTTP_400_BAD_REQUEST)
            file_name = f"{uuid.uuid4()}.{image_type}"
            file = ContentFile(decoded_image, name=file_name)
            user.avatar.save(file.name, file)
            user.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = f'Ошибка при обработке изображения: {str(e)}'
            return Response({'avatar': error_message},
                            status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        if user.avatar:
            user.avatar.delete(save=True)
            return Response({'detail': 'Аватар успешно удалён'},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': 'У пользователя нет аватара'},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_profile(request, id):
    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        return Response({'detail': 'Страница не найдена.'}, status=404)
    serializer = UserGetSerializer(user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = request.user
    serializer = UserGetSerializer(user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_subscriptions(request):
    user = request.user
    recipes_limit = int(request.query_params.get('recipes_limit', 5))

    subscriptions = Subscription.objects.filter(subscriber=user)

    authors = [subscription.author for subscription in subscriptions]

    paginator = CustomPagination()
    result_page = paginator.paginate_queryset(authors, request)

    user_data = []
    for author in result_page:
        filtered_recipes = (Recipe.objects
                            .filter(author=author)
                            .order_by('-created_at'))
        recipes = filtered_recipes[:recipes_limit]
        recipes_data = RecipeShortSerializer(recipes, many=True).data

        user_data.append({
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': True,
            'avatar': author.avatar.url if author.avatar else None,
            'recipes': recipes_data,
            'recipes_count': recipes.count(),
        })

    return paginator.get_paginated_response(user_data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_subscription(request, id):
    user = request.user

    try:
        author = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        if user.id == author.id:
            return Response({'detail': 'Нельзя подписаться на себя'},
                            status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(subscriber=user,
                                       author=author).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscription.objects.create(subscriber=user, author=author)

        recipes_limit = int(request.query_params.get('recipes_limit', 5))
        recipes = Recipe.objects.filter(author=author)[:recipes_limit]
        recipes_data = RecipeShortSerializer(recipes, many=True).data

        user_data = {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': True,
            'recipes': recipes_data,
            'recipes_count': recipes.count(),
            'avatar': author.avatar.url if author.avatar else None,
        }

        return Response(user_data, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        subscription = Subscription.objects.filter(subscriber=user,
                                                   author=author).first()
        if not subscription:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
