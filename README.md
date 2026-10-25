# Менеджер задач — REST API на FastAPI

![CI](https://github.com/MaksChocomint/fastapi-tasks/actions/workflows/ci.yml/badge.svg)

Сервис хранит пользователей и их задачи в PostgreSQL и предоставляет REST API.
Стек: FastAPI, SQLAlchemy 2.0 (async, asyncpg), Pydantic v2, pydantic-settings, Alembic,
pytest, Docker, GitHub Actions.

- Практическая работа № 2 — сам сервис: разделы «Запуск», «Скриншоты» и
  [ответы на вопросы ПЗ2](#контрольные-вопросы-пз2).
- Практическая работа № 3 — тесты, Docker-образ и CI/CD: раздел
  [«ПЗ3: тесты, Docker и CI/CD»](#пз3-тесты-docker-и-cicd).

Опубликованный образ:

- GitHub Container Registry: <https://github.com/MaksChocomint/fastapi-tasks/pkgs/container/fastapi-tasks>
  (`docker pull ghcr.io/makschocomint/fastapi-tasks:latest`)
- Docker Hub: <https://hub.docker.com/r/maksimchocomint/fastapi-tasks>
  (`docker pull maksimchocomint/fastapi-tasks:latest`)

## Структура

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py          # приложение, middleware, подключение роутеров
│   ├── config.py        # настройки (pydantic-settings), DATABASE_URL
│   ├── db.py            # асинхронный движок, фабрика сессий, Base, get_session
│   ├── models.py        # ORM-модели User и Task
│   ├── schemas.py       # Pydantic-схемы *Create, *Read, *Update
│   └── routers/
│       ├── users.py
│       └── tasks.py
├── migrations/          # Alembic (шаблон async), первая миграция в versions/
├── tests/               # pytest: conftest.py (фикстуры), test_users.py, test_tasks.py
├── .github/workflows/
│   └── ci.yml           # CI: lint → test → build (публикация образа)
├── alembic.ini
├── Dockerfile           # многоэтапная сборка, запуск от пользователя app
├── docker-compose.yml   # db + app (миграции перед стартом) + tests
├── requirements.txt
├── requirements-dev.txt # pytest, pytest-asyncio, httpx, ruff
├── pytest.ini
├── ruff.toml
├── .env.example
└── README.md
```

## Эндпоинты

| Метод | Путь | Описание | Коды ответа |
| --- | --- | --- | --- |
| POST | `/users` | создать пользователя | 201, 409 (email занят), 422 |
| GET | `/users/{id}` | получить пользователя | 200, 404 |
| POST | `/tasks` | создать задачу | 201, 404 (нет владельца), 422 |
| GET | `/tasks` | список задач, фильтры `done`, `owner_id`, пагинация `limit` (1–100), `offset` | 200 |
| GET | `/tasks/{id}` | получить задачу | 200, 404 |
| PATCH | `/tasks/{id}` | частично обновить задачу | 200, 404, 422 |
| DELETE | `/tasks/{id}` | удалить задачу | 204, 404 |

Каждый ответ содержит заголовок `X-Process-Time`, а в лог пишется строка вида
`INFO app: GET /tasks/1 200 0.0035 s`.

## Запуск

Нужны Python 3.11+, Docker и Docker Compose.

1. Клонировать репозиторий:

   ```bash
   git clone https://github.com/MaksChocomint/fastapi-tasks.git
   cd fastapi-tasks
   ```

2. Создать файл с настройками:

   ```bash
   cp .env.example .env          # Windows: copy .env.example .env
   ```

   Если порт 5432 уже занят (например, локальным PostgreSQL), поменяйте в `.env` порт
   в `DB_PORT` и в `DATABASE_URL`, например на 5434.

3. Запустить PostgreSQL и проверить, что база отвечает:

   ```bash
   docker compose up -d db
   docker compose exec db psql -U app -d tasks -c "select 1"
   ```

4. Создать виртуальное окружение и установить зависимости:

   ```bash
   python -m venv .venv
   source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. Применить миграции (таблицы создаёт Alembic, не `create_all`):

   ```bash
   alembic upgrade head
   ```

6. Запустить сервис:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Открыть Swagger UI: <http://127.0.0.1:8000/docs>

Как создавалась миграция (повторять не нужно, она уже в `migrations/versions/`):

```bash
alembic init -t async migrations
alembic revision --autogenerate -m "create users and tasks"
```

## Скриншоты

### Swagger UI

Все эндпоинты:

![Swagger UI](img/swagger-all.png)

Создание пользователя — 201:

![POST /users](img/post-users-201.png)

Создание задачи — 201:

![POST /tasks](img/post-tasks-201.png)

Получение задачи — 200:

![GET /tasks/{id}](img/get-task-200.png)

Частичное обновление задачи — 200 (в заголовках ответа виден `x-process-time`):

![PATCH /tasks/{id}](img/patch-task-200.png)

Удаление задачи — 204:

![DELETE /tasks/{id}](img/delete-task-204.png)

Запрос несуществующей задачи — 404:

![GET /tasks/{id} 404](img/get-task-404.png)

### Таблицы в БД

```bash
docker compose exec db psql -U app -d tasks -c "\dt"
```

![Таблицы в psql](img/psql-dt.png)

## Контрольные вопросы ПЗ2

**1. Чем FastAPI отличается от Starlette и какие компоненты Starlette он использует?**

Starlette — это лёгкий ASGI-фреймворк: маршрутизация, запросы и ответы, middleware,
WebSocket, фоновые задачи, тестовый клиент. FastAPI построен поверх Starlette (класс
`FastAPI` наследуется от `Starlette`) и добавляет то, чего в Starlette нет: валидацию
входных данных и сериализацию ответов через Pydantic по аннотациям типов, систему
зависимостей `Depends`, автоматическую генерацию OpenAPI-схемы и документации
(Swagger UI, ReDoc). Из Starlette FastAPI использует `Request`, `Response` и их
разновидности, роутинг, middleware (в этой работе — `BaseHTTPMiddleware`),
`BackgroundTasks`, `HTTPException` (FastAPI расширяет его), `TestClient`, `StaticFiles`.

**2. Зачем разделять схемы Create, Read и Update?**

У каждой операции свой набор полей и свои правила. При создании клиент не передаёт `id`
и `created_at` — их назначает база, а обязательные поля (`title`, `owner_id`) должны быть.
При чтении, наоборот, `id` и `created_at` возвращаются. При обновлении все поля
необязательны, потому что клиент меняет только часть. Если сделать одну общую схему,
то либо клиент сможет подсунуть `id`, либо придётся делать всё необязательным и терять
валидацию. Кроме того, Read-схема определяет, что уходит наружу, и защищает от
случайной выдачи служебных полей.

**3. Что делает `from_attributes=True`?**

Разрешает Pydantic создавать модель из произвольного объекта, читая его атрибуты
(`obj.id`, `obj.title`), а не только из словаря. Благодаря этому из эндпоинта можно
вернуть ORM-объект SQLAlchemy, и FastAPI сам превратит его в `TaskRead`
(`TaskRead.model_validate(task)`). В Pydantic v1 эта настройка называлась `orm_mode`.

**4. Почему сессия передаётся через `Depends`, а не создаётся глобально?**

Сессия SQLAlchemy не потокобезопасна и хранит состояние (транзакцию, загруженные
объекты), поэтому одна глобальная сессия на все параллельные запросы привела бы
к смешиванию транзакций и ошибкам. Через `Depends(get_session)` каждый запрос получает
свою сессию, а код после `yield` гарантированно закрывает её, даже если в обработчике
возникло исключение. Ещё одна причина — тестируемость: в тестах зависимость легко
подменить через `app.dependency_overrides`, например на сессию к тестовой базе.

**5. Чем `exclude_unset=True` отличается от `exclude_none=True`?**

`exclude_unset=True` выбрасывает поля, которые клиент вообще не передал в запросе.
`exclude_none=True` выбрасывает поля, значение которых равно `None`, неважно, передал
их клиент или нет. Для PATCH нужен `exclude_unset`: запрос `{"done": true}` должен
изменить только `done`, а запрос `{"description": null}` — явно очистить описание.
С `exclude_none` второй запрос ничего бы не сделал, потому что `None` был бы отброшен.

**6. Почему в production таблицы не создают через `create_all`?**

`create_all` только создаёт отсутствующие таблицы и ничего не делает с уже существующими:
не добавит новый столбец, не поменяет тип, не удалит индекс. В работающей базе с данными
схема меняется постепенно, и каждое изменение нужно применять одинаково на всех стендах.
Миграции Alembic хранят историю изменений в репозитории, их можно просмотреть
на ревью, применить (`upgrade`) и откатить (`downgrade`), а таблица `alembic_version`
показывает, какая версия схемы сейчас в базе.

## ПЗ3: тесты, Docker и CI/CD

### Тесты

12 тестов в `tests/` работают с настоящей PostgreSQL, с отдельной базой `tasks_test`.
Фикстура создаёт базу, если её нет, перед каждым тестом очищает таблицы
(`TRUNCATE ... RESTART IDENTITY`) и подменяет `get_session` через
`app.dependency_overrides`, чтобы приложение работало с тестовой базой.

| № | Тест | Что проверяет |
| --- | --- | --- |
| 1 | `test_create_user` | создание пользователя — 201 |
| 2 | `test_duplicate_email` | повторный email — 409 |
| 3 | `test_invalid_email` | невалидный email — 422 |
| 4 | `test_create_task` | создание задачи — 201 |
| 5 | `test_create_task_missing_owner` | несуществующий владелец — 404 |
| 6 | `test_filter_done_and_pagination` | фильтр `done`, `limit`/`offset`, `limit=101` → 422 |
| 7 | `test_patch_changes_only_given_fields` | PATCH меняет только переданные поля |
| 8 | `test_delete_then_get_returns_404` | DELETE → 204, затем GET → 404 |
| 9 | `test_process_time_header` | заголовок `X-Process-Time` |
| + | `test_get_user`, `test_get_missing_user`, `test_create_task_empty_title` | 200 и 404 для пользователя, пустой `title` → 422 |

**Запуск тестов локально** (нужна запущенная база из `docker compose up -d db`):

```bash
pip install -r requirements-dev.txt
pytest -v
```

По умолчанию тесты подключаются к `postgresql+asyncpg://app:app@localhost:5432/tasks_test`.
Если PostgreSQL на другом порту, адрес задаётся переменной `TEST_DATABASE_URL`:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://app:app@localhost:5434/tasks_test pytest -v
# PowerShell:
# $env:TEST_DATABASE_URL="postgresql+asyncpg://app:app@localhost:5434/tasks_test"; pytest -v
```

**Запуск тестов через Docker Compose** (ничего, кроме Docker, не нужно):

```bash
docker compose --profile test run --rm --build tests
```

Линтер:

```bash
ruff check .
ruff format --check .
```

### Docker

`Dockerfile` — многоэтапная сборка:

1. `builder` — ставит зависимости из `requirements.txt` в отдельный каталог;
2. `runtime` — чистый `python:3.13-slim`, в который копируются только установленные
   пакеты и код приложения; процесс запускается от пользователя `app` (uid 1000);
3. `test` — `runtime` + dev-зависимости и тесты, используется для запуска тестов в Compose.

`docker-compose.yml` поднимает всё приложение:

- `db` — PostgreSQL 16 с `healthcheck` (`pg_isready`);
- `app` — ждёт, пока `db` станет healthy (`depends_on: condition: service_healthy`),
  применяет миграции `alembic upgrade head` и запускает uvicorn;
- `tests` — запускается только с профилем `test`.

```bash
docker compose up -d --build     # приложение на http://127.0.0.1:8000/docs
docker compose logs app          # видно, что миграции применились до старта uvicorn
docker compose down
```

### CI/CD

`.github/workflows/ci.yml` запускается на каждый push и pull request:

```text
push / pull_request
  ├─ lint   ruff check + ruff format --check
  ├─ test   PostgreSQL как service-контейнер + pytest
  └─ build  needs: [lint, test], только push в main
            → образ в ghcr.io/makschocomint/fastapi-tasks и в Docker Hub
```

Для публикации в GHCR используется встроенный `GITHUB_TOKEN` с правом `packages: write`.
Для Docker Hub — секреты репозитория `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`
(Access Token из настроек Docker Hub). Образ получает теги `latest` и хеш коммита.

### Проверка: pull request с упавшим тестом

Успешный pipeline при push в `main`: все три job зелёные, `build` опубликовал образ
в GHCR и Docker Hub.

![Успешный pipeline](img/ci-success.png)

Для проверки создана ветка `broken-test`: в `test_create_user` ожидаемый код намеренно
заменён на 200 вместо 201. По ней открыт
[pull request #1](https://github.com/MaksChocomint/fastapi-tasks/pull/1).
Pipeline стал красным: `lint` прошёл, `test` упал с `assert 201 == 200`, а `build`
пропущен, потому что зависит от `test` (`needs`):

![Упавший pipeline в pull request](img/ci-failed-pr.png)

![Упавший pipeline в Actions](img/ci-failed.png)

После этого тест исправлен в той же ветке, pipeline стал зелёным, и pull request
влит в `main`.

### Контрольные вопросы ПЗ3

**1. Чем CI отличается от CD (continuous delivery и continuous deployment)?**

CI (continuous integration, непрерывная интеграция) — каждое изменение автоматически
собирается и проверяется линтером и тестами, чтобы ошибки находились сразу, а не при
слиянии большого объёма кода. CD продолжает CI. Continuous delivery (непрерывная
поставка) — после проверок автоматически собирается готовый к выкладке артефакт
(в этой работе — Docker-образ в реестре), но выкладка в production запускается
вручную. Continuous deployment (непрерывное развёртывание) — выкладка в production
тоже автоматическая, без участия человека: каждый зелёный коммит в `main` сразу
попадает к пользователям.

**2. Как работает `dependency_overrides` и зачем он нужен в тестах?**

`app.dependency_overrides` — словарь «исходная зависимость → замена». Когда FastAPI
разрешает `Depends(get_session)`, он сначала смотрит в этот словарь и, если там есть
замена, вызывает её. В тестах это позволяет не трогать код приложения, но подсунуть ему
сессию к тестовой базе `tasks_test` вместо рабочей. Так же подменяют внешние сервисы,
авторизацию и т. п. После теста словарь очищается (`dependency_overrides.clear()`).

**3. Зачем нужна многоэтапная сборка образа?**

Чтобы в финальный образ попало только то, что нужно для запуска. В первом этапе
можно ставить компиляторы, заголовочные файлы, кэш pip, собирать колёса, а финальный
этап копирует из него только результат. Образ получается меньше (здесь — около 300 МБ
на базе `python:3.13-slim`), быстрее скачивается, и в нём меньше пакетов, в которых могут
быть уязвимости. Кроме того, из одного Dockerfile можно собирать разные цели: у нас
`runtime` для production и `test` для тестов.

**4. Почему контейнер не следует запускать от root?**

Root внутри контейнера — это тот же uid 0, что и на хосте, изоляция обеспечивается
только механизмами ядра. Если в приложении найдут уязвимость (например, выполнение
произвольного кода), злоумышленник получит права root в контейнере: сможет менять
любые файлы образа, ставить программы, а при ошибке конфигурации (смонтированный
`docker.sock`, `--privileged`, уязвимость ядра) — выбраться на хост. От
непривилегированного пользователя ущерб ограничен его правами. Принцип минимальных
привилегий: приложению для работы root не нужен.

**5. Как в GitHub Actions передаются секреты и почему их нельзя хранить в репозитории?**

Секреты задаются в настройках репозитория (Settings → Secrets and variables → Actions),
хранятся в зашифрованном виде и подставляются в workflow через
`${{ secrets.ИМЯ }}`. В логах их значения автоматически заменяются на `***`, а в
workflow, запущенные из форков, они не передаются. Токен `GITHUB_TOKEN` создаётся
автоматически на каждый запуск и действует только в нём. В репозитории секреты хранить
нельзя: их увидит каждый, у кого есть доступ к коду (а для публичного репозитория — весь
интернет), они останутся в истории git даже после удаления файла, попадут в форки
и клоны. Утёкший токен Docker Hub позволил бы опубликовать от нашего имени
вредоносный образ.

**6. Что произойдёт с job-ом `build`, если упадёт `test`? Где это задаётся?**

`build` не запустится — в интерфейсе он будет помечен как пропущенный (skipped),
образ не соберётся и не опубликуется. Это задаётся ключом `needs: [lint, test]` у job
`build`: job стартует только после успешного завершения всех перечисленных job.
Дополнительно условие `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`
не даёт собирать образ для pull request и других веток.

**7. Где лучше применять миграции: при старте контейнера или отдельным шагом в CD?**

| | При старте контейнера | Отдельный шаг в CD |
| --- | --- | --- |
| Плюсы | просто, ничего не нужно настраивать; схема всегда соответствует запущенному коду; удобно для разработки и одной копии сервиса | миграция выполняется один раз и до выкладки новой версии; если она упала, новая версия не выкладывается; можно сделать резервную копию перед миграцией; приложению не нужны права на изменение схемы |
| Минусы | при нескольких репликах миграцию одновременно запустят все контейнеры (гонка, блокировки); долгая миграция задерживает старт, а healthcheck может посчитать контейнер упавшим; ошибка миграции превращается в постоянный перезапуск контейнера | нужен отдельный шаг или job и доступ из CD к базе; нужно следить, чтобы код был совместим со схемой до и после миграции |

В этой работе миграции применяются при старте контейнера (`alembic upgrade head` в
команде сервиса `app`) — это нормально для одного экземпляра и учебного стенда.
Для production с несколькими репликами лучше отдельный шаг в CD (или отдельный
одноразовый контейнер/job с миграцией) перед обновлением приложения.
