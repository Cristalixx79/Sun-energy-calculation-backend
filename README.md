# Vibes — Solar Panels Service (Лабораторная работа №3)

Backend REST API на FastAPI для сервиса объявлений об аренде/продаже
солнечных панелей. Бэкенд рассчитан на использование из SPA и
тестирование через Insomnia/Postman (JSON, без серверного рендеринга
HTML).

## Структура проекта

```
main.py                    # точка входа, подключение роутеров /api/...
api/
  services.py               # домен "услуга": все 7 методов
  users.py                  # домен "пользователь": регистрация + заглушки
  common.py                 # общие SQL-запросы и сериализация Service -> JSON
core/
  config.py                 # настройки (БД, Minio), читаются из окружения
  current_user.py           # singleton текущего пользователя (см. ниже)
  security.py                # хэширование паролей (PBKDF2)
db/
  base.py                    # DeclarativeBase
  session.py                 # async engine/session, get_db()
models/
  user.py, service.py, like.py
schemas/
  service.py, user.py        # Pydantic-схемы запросов/ответов
storage/
  minio_client.py             # загрузка файлов в Minio, генерация имён
alembic/
  env.py
frontend_legacy/             # старые Jinja2-шаблоны, НЕ подключены к main.py
```

## Запуск

1. `pip install -r requirements.txt`
2. Скопировать `.env.example` в `.env` и при необходимости поправить
   параметры БД/Minio (или экспортировать переменные окружения).
3. Поднять PostgreSQL и Minio (например через docker-compose — в
   проекте не зафиксирован, добавьте под свою инфраструктуру).
4. Создать бакет в Minio не обязательно вручную — `storage/minio_client.py`
   создаёт его при первом обращении, если он не существует.
5. Прогнать миграции: `alembic revision --autogenerate -m "init"` и
   `alembic upgrade head` (структура моделей поменялась относительно
   предыдущей лабораторной — понадобится новая ревизия).
6. Запустить сервер: `python main.py` (или `uvicorn main:solar_panels_app --reload`).
7. Swagger-документация доступна на `/docs`.

## Таблицы БД

### `users`
| Поле | Тип | Описание |
|---|---|---|
| id | int, PK | системное |
| username | varchar(50), unique | логин |
| password_hash | varchar(255) | PBKDF2-хэш пароля, не сам пароль |

### `services`
| Поле | Тип | Описание |
|---|---|---|
| id | int, PK | системное |
| title | varchar(100) | название |
| description | varchar(500) | описание |
| status | varchar(20) | `draft` \| `published` \| `deleted` — системное, меняется только бизнес-логикой |
| image_filename | varchar(255), nullable | имя файла-изображения в Minio (генерируется на латинице) |
| video_filename | varchar(255), nullable | имя файла-видео в Minio (генерируется на латинице) |
| kpd | int, nullable | КПД панели, % |
| price | float, nullable | цена, ₽/м² |
| creator_id | int, FK -> users.id | системное, берётся из singleton текущего пользователя |
| created_at | timestamptz | системное |
| updated_at | timestamptz | системное |

### `likes`
| Поле | Тип | Описание |
|---|---|---|
| id | int, PK | системное |
| user_id | int, FK -> users.id | кто поставил лайк |
| service_id | int, FK -> services.id | какой услуге |
| — | UNIQUE(user_id, service_id) | один пользователь — один лайк на услугу |

Записи `services` со статусом `deleted` никогда не возвращаются
клиенту ни одним из методов.

## HTTP API

Все методы — под префиксом `/api`. Текущий пользователь везде берётся
через singleton-функцию `core.current_user.get_current_user_id()` —
отдельного параметра `user_id` в запросах нет, как и не должно быть.

### Домен «услуга» — `/api/services`

| Метод | URL | Тело запроса | Ответ | Описание |
|---|---|---|---|---|
| GET | `/api/services?kpd_below_than=25` | — | `ServiceListItem[]` | Список **только опубликованных** услуг с фильтром по КПД. Каждый элемент содержит `is_own` (1/0 — совпадает ли создатель с текущим пользователем) |
| GET | `/api/services/feed` | — | `ServiceOut` | Лента: первая опубликованная услуга, id не указывается |
| GET | `/api/services/feed/{id}?next=true` | — | `ServiceOut` | Лента с конкретной услуги; с `next=true` — следующая опубликованная по кругу |
| GET | `/api/services/draft` | — | `ServiceOut \| null` | Черновик текущего пользователя (не более одного), id не указывается |
| POST | `/api/services` | `multipart/form-data`: `title`, `image` (файл), `video` (файл) | `ServiceOut`, 201 | Создание черновика + загрузка файлов в Minio. 409, если черновик уже есть |
| PUT | `/api/services/{id}/publish` | JSON: `title?`, `description`, `kpd`, `price` | `ServiceOut` | Публикация: `draft -> published`. 404 — не ваш черновик, 409 — уже не `draft` |
| DELETE | `/api/services/{id}` | — | 204 | Soft delete (`status = deleted`), только свои услуги, через ORM |
| POST | `/api/services/{id}/like` | JSON: `{"value": 0 \| 1}` | `LikeOut` | `value=1` — поставить лайк, `value=0` — снять |

### Домен «пользователь» — `/api/users`

| Метод | URL | Тело запроса | Ответ | Описание |
|---|---|---|---|---|
| POST | `/api/users/register` | JSON: `username`, `password` | `UserOut`, 201 | Регистрация. 409, если логин занят |
| POST | `/api/users/login` | JSON: `username`, `password` | `{"detail": ...}` | Заглушка — полноценная аутентификация будет в лаб. №4 |
| POST | `/api/users/logout` | — | `{"detail": ...}` | Заглушка деавторизации (лаб. №4) |

## Бизнес-правила, которые заложены в код

- **Системные поля** (`id`, `status`, `creator_id`, `created_at`,
  `updated_at`) никогда не принимаются из тела запроса — они либо
  генерируются БД, либо выставляются на бэкенде из singleton
  текущего пользователя.
- **Переходы статусов однонаправленные**: создание всегда даёт
  `draft`, `publish` — только `draft -> published`, `delete` — из
  любого не-`deleted` статуса в `deleted`. Обратного пути в `draft`
  нет ни одним методом.
- **Только ORM** — SQL-запрос через `text()` (как было в предыдущей
  версии `delete_service`) убран, удаление теперь идёт через
  SQLAlchemy ORM.
- **Файлы, а не URL** — `image`/`video` в `POST /api/services`
  принимаются как файлы (`UploadFile`), реально загружаются в Minio,
  а в БД остаётся только сгенерированное имя объекта (латиница,
  `uuid4().hex` + исходное расширение).
