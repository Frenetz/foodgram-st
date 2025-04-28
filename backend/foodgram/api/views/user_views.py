from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewSet
from ..serializers.user_serializers import (
    UserGetSerializer,
    SubscriptionUserSerializer
)
from recipes.models import Subscription
import base64
import uuid
import imghdr
from django.core.files.base import ContentFile


class UserViewSet(DjoserUserViewSet):
    queryset = get_user_model().objects.all().prefetch_related(
        'recipes', 'subscriptions__author', 'subscribers__subscriber'
    ).order_by('id')

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = UserGetSerializer(
            user,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response({'avatar': ['Это поле обязательно.']},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                if isinstance(avatar_data, str) and "base64," in avatar_data:
                    format, imgstr = avatar_data.split(';base64,')
                else:
                    return Response(
                        {'avatar': ['Ожидается строка в формате Base64.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                decoded_image = base64.b64decode(imgstr)
                image_type = imghdr.what(None, decoded_image)

                if image_type not in ['jpeg', 'png', 'gif']:
                    return Response(
                        {
                            'avatar': [
                                'Неверный формат изображения '
                                '(допустимы JPEG, PNG, GIF).'
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                file_name = f"{uuid.uuid4()}.{image_type}"
                file = ContentFile(decoded_image, name=file_name)

                if user.avatar:
                    user.avatar.delete(save=False)

                user.avatar.save(file.name, file, save=True)

                avatar_url = request.build_absolute_uri(user.avatar.url)
                return Response(
                    {'avatar': avatar_url},
                    status=status.HTTP_200_OK
                )

            except (base64.binascii.Error, TypeError, ValueError) as e:
                return Response(
                    {'avatar': [f'Ошибка декодирования Base64: {str(e)}']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                error_message = f'Ошибка при обработке изображения: {str(e)}'
                return Response({'avatar': [error_message]},
                                status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'detail': 'У пользователя нет аватара для удаления.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = (
            user.subscriptions.all()
            .select_related('author')
            .prefetch_related('author__recipes')
        )

        page = self.paginate_queryset(queryset)

        authors_on_page = [subscription.author for subscription in page]
        serializer = SubscriptionUserSerializer(
            authors_on_page,
            many=True,
            context=self.get_serializer_context()
        )

        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(get_user_model(), id=id)

        if request.method == 'POST':
            if user.id == author.id:
                return Response({'errors': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)

            subscription, created = Subscription.objects.get_or_create(
                subscriber=user, author=author
            )

            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionUserSerializer(
                author, context=self.get_serializer_context()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                subscriber=user, author=author
            ).first()
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'errors': 'Вы не были подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
