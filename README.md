# Foodgram  
«Фудграм» — сайт для публикации рецептов, добавления их в избранное и подписки на авторов.  

### Тестирование (через Postman)  
1. Клонировать: `git clone git@github.com:Frenetz/foodgram-st.git`  
2. Перейти в директорию с проектом: `cd foodgram-st/backend/foodgram`  
3. Виртуальное окружение:  
    ```bash 
    python3 -m venv venv  
    source ./env/bin/activate
    ```
4. Установка зависимостей:
    ```bash
    pip install -r requirements.txt
    ```
5. Создание `.env` файла на основе `.env.example`
6. Сгенерируйте `SECRET_KEY`, а также установите `DEBUG = True`
7. Выполните миграции:
    ```bash
    python3 manage.py migrate
    ```
8. Создайте суперпользователя:
    ```bash
    python3 manage.py createsuperuser
    ```
9. Загрузите статику:
    ```bash
    python3 manage.py collectstatic --no-input
    ```
10. Заполните БД инградиентами:
    ```bash
    python3 manage.py load_ingredients
    ```
11. Запустите встроенный сервер:
    ```bash
    python3 manage.py runserver 8000
    ```

### Запуск проекта через Docker
1. Клонировать проект `git@github.com:Frenetz/foodgram-st.git`
2. Перейти в директорию с проектом `cd foodgram-st/backend/foodgram`
3. Настройка виртуального окружения:
    ```bash
    python3 -m venv venv
    source ./env/bin/activate
    ```
4. Создание `.env` файла на основе `.env.example`
5. Сгенерируйте `SECRET_KEY`, а также установите `DEBUG = False`
6. Запуск проекта:
    ```bash
    docker-compose up -d
    ```
7. Миграции:
    ```bash
    docker exec foodgram-back python manage.py migrate
    ```
8. Создание суперпользователя:
    ```bash
    docker exec -it foodgram-back python3 manage.py createsuperuser
    ```
9. Добавление инградиентов:
    ```bash
    docker-compose exec backend python3 manage.py load_ingredients
    ```
10. Сборка статики:
    ```bash
    docker-compose exec backend python manage.py collectstatic
    ```