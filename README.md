# Solar Panels Service (Лабораторные работы №3–4)

Backend REST API на FastAPI для SPA «Vibes» — сервис объявлений о
солнечных панелях. Данные — PostgreSQL (SQLAlchemy ORM), файлы —
Minio, сессии — Redis. Авторизация: серверные сессии + cookie.

## Структура проекта

```
main.py                    # точка входа, роутеры /api/..., описание Swagger
api/
  services.py               # домен "услуга": 7 методов
  users.py                  # домен "пользователь": регистрация, вход, выход
  common.py                 # общие SQL-запросы и сериализация Service -> JSON
core/
  config.py                 # настройки (БД, Minio, Redis, cookie), из окружения
  auth.py                   # зависимости авторизации (сессия из cookie)
  security.py               # хэширование паролей (PBKDF2)
db/                         # DeclarativeBase, async engine/session
models/                     # User, Service, Like (SQLAlchemy)
schemas/                    # Pydantic-схемы запросов/ответов (service, user, common)
storage/
  minio_client.py           # загрузка файлов в Minio
  session_store.py          # сессии в Redis
alembic/env.py
frontend_legacy/            # старые Jinja2-шаблоны, не подключены
```

## Запуск

1. `pip install -r requirements.txt`
2. Скопировать `.env.example` в `.env`, при необходимости поправить параметры.
3. Поднять PostgreSQL, Minio и Redis, например Redis:
   `docker run -p 6379:6379 redis`
4. Миграции: `alembic upgrade head` (модели в лаб. №4 не менялись).
5. Запуск: `python main.py` (или `uvicorn main:solar_panels_app --reload`).
6. Swagger: `http://127.0.0.1:8000/docs`.

## Авторизация (лаб. №4)

Схема: сессии на сервере + идентификатор сессии в cookie.

1. `POST /api/users/login` проверяет логин и пароль, создаёт в Redis ключ
   `session:<session_id>` со значением `{"user_id": ..., "username": ...}`
   и временем жизни `SESSION_TTL_SECONDS`, а в ответе выставляет cookie
   `session_id` (HttpOnly, SameSite=Lax).
2. Браузер отправляет cookie с каждым запросом; `core/auth.py` по
   session_id находит пользователя в Redis.
3. `POST /api/users/logout` удаляет ключ из Redis и очищает cookie.
4. Создатель услуги (`creator_id`) подставляется автоматически из сессии —
   замена singleton-функции из лаб. №3.

Методы чтения (список, лента) работают одинаково с cookie и без неё; поле
`is_own` для гостя всегда 0. Методы создателя без сессии возвращают `401`,
для чужой услуги — `403`.

### Swagger

В Swagger методы создателя помечены замком (схема `SessionCookie`), у каждого
метода есть описание, примеры тел запросов и возможные коды ответов. Порядок
показа: открыть `/docs` в режиме инкогнито → выполнить `POST /api/users/login`
→ браузер сохранит cookie → выполнять методы создателя.

### Insomnia / Postman

Значение cookie `session_id` скопировать из браузера (DevTools → Application →
Cookies) в заголовок `Cookie: session_id=<значение>`; либо сначала выполнить
`POST /api/users/login` в самом клиенте — он сохранит cookie сам.

### Проверка Redis

```
redis-cli
KEYS session:*
GET session:<session_id>     # {"user_id": 1, "username": "test_user"}
TTL session:<session_id>
```

## Таблицы БД

### `users`
| Поле | Тип | Описание |
|---|---|---|
| id | int, PK | системное |
| username | varchar(50), unique | логин |
| password_hash | varchar(255) | PBKDF2-хэш пароля |

### `services`
| Поле | Тип | Описание |
|---|---|---|
| id | int, PK | системное |
| title | varchar(100) | название |
| description | varchar(500) | описание |
| status | varchar(20) | `draft` \| `published` \| `deleted` — системное |
| image_filename | varchar(255), nullable | имя файла изображения в Minio |
| video_filename | varchar(255), nullable | имя файла видео в Minio |
| kpd | int, nullable | КПД, % |
| price | float, nullable | цена, ₽/м² |
| creator_id | int, FK -> users.id | системное, из сессии |
| created_at, updated_at | timestamptz | системные |

### `likes`
| Поле | Тип | Описание |
|---|---|---|
| id | int, PK | системное |
| user_id | int, FK -> users.id | кто поставил |
| service_id | int, FK -> services.id | какой услуге |
| — | UNIQUE(user_id, service_id) | один лайк на пользователя |

## HTTP API

Все методы — под префиксом `/api`. «Гость» — без сессии, «Создатель» — с сессией.

| № | Метод | URL | Доступ | Описание |
|---|---|---|---|---|
| 1 | POST | `/api/users/register` | все | Регистрация |
| 2 | POST | `/api/users/login` | все | Аутентификация, создаёт сессию и cookie |
| 3 | POST | `/api/users/logout` | создатель | Деавторизация, удаляет сессию |
| 4 | GET | `/api/services?kpd_below_than=` | все | Список опубликованных услуг с фильтром по КПД |
| 5 | GET | `/api/services/feed` | все | Лента: первая опубликованная услуга |
| 6 | GET | `/api/services/feed/{id}?next=true` | все | Лента: услуга по id или следующая |
| 7 | GET | `/api/services/draft` | создатель | Черновик текущего пользователя |
| 8 | POST | `/api/services` | создатель | Добавление (multipart: title, image, video) |
| 9 | PUT | `/api/services/{id}/publish` | создатель | Публикация: draft -> published |
| 10 | DELETE | `/api/services/{id}` | создатель | Soft delete своей услуги |
| 11 | POST | `/api/services/{id}/like` | создатель | Лайк (`value`: 1 — поставить, 0 — снять) |

## Бизнес-правила

- Системные поля (`id`, `status`, `creator_id`, даты) не принимаются от клиента.
- Статусы меняются только вперёд: `draft -> published -> deleted`.
- Записи со статусом `deleted` клиенту не отдаются.
- Только ORM, без сырого SQL.
- Файлы загружаются в Minio под сгенерированными латинскими именами.
- Если Redis недоступен, методы, обращающиеся к сессии, возвращают `503`.
