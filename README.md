# Delivery Route Optimizer

REST-сервис для управления заказами службы доставки и построения (почти) оптимального маршрута объезда для курьеров.

## Автор

Артур Саларидзе, salaridze.ae@phystech.edu

## Возможности

- Регистрация и аутентификация пользователей (менеджеры, курьеры).
- Управление точками выдачи заказов (CRUD).
- Создание и отслеживание заказов с назначением курьера.
- Построение оптимального маршрута для курьера (Cheapest Insertion + 2-opt).
- Изменение статуса заказов: новый > в доставке > доставлен.
- Автоматическое тестирование (покрытие 82%).

## Технологии

- **FastAPI** – веб-фреймворк
- **SQLModel** – ORM и валидация данных
- **SQLite** – база данных (файловая, без Docker)
- **JWT (python-jose)** – аутентификация по токену
- **Pydantic Settings** – конфигурация из .env
- **Passlib + bcrypt** – хеширование паролей
- **Pytest + TestClient** – автоматические тесты

## Установка и запуск

Клонируйте репозиторий:
   ```bash
   git clone https://github.com/artur0513/python_fastapi_prj
   cd python_fastapi_prj
   ```
   
Создайте виртуальное окружение и активируйте его:
   ```bash 
   python -m venv .venv
   source .venv/bin/activate        # для Linux/Mac
   .venv\Scripts\activate           # для Windows
   ```

Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```
Создайте файл .env в корне проекта со следующим содержимым:

   ```text
   SECRET_KEY=ваш-секретный-ключ-сюда
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   DATABASE_URL=sqlite:///./delivery.db
   ```
Запустите сервер:

   ```bash
   uvicorn app.main:app --reload
   ```

Сервер будет доступен по адресу http://127.0.0.1:8000.
Документация Swagger: http://127.0.0.1:8000/docs.
   

## Как пользоваться

Через Swagger. Откройте /docs, сначала зарегистрируйте пользователей:

POST /auth/signup — укажите role: "manager" и role: "courier".

Залогиньтесь под каждым, скопируйте access_token. 
Нажмите кнопку Authorize и вставьте токен в формате Bearer <токен>.

Менеджер:
Создаёт точки выдачи (POST /pickup-points). 
Создаёт заказы (POST /orders), указывая ID курьера и ID точки.

Курьер:
Обновляет свои координаты (PUT /users/me/coords). 
Запрашивает оптимальный маршрут (GET /courier/route) — статусы заказов меняются на in_delivery. 
Отмечает заказ доставленным (POST /courier/complete-order/{order_id}).

Для создания тестовой базы данных можно воспользоваться seed_data.py после запуска сервера. 
Скрипт выведет в консоль информацию для логина в систему.

## Тестирование
Для запуска тестов с оценкой покрытия выполнить:

   ```bash
   pytest --cov=app --cov-report=term-missing
   ```
Все тесты расположены в папке tests/.

## Проверка качества кода
   ```bash
   pylint app > pylint.txt
   ```
