# MIPT HW2/HW3 WEB — интернет-магазин светотехники

Репозиторий содержит исправленную backend-часть из домашнего задания 2 и готовую пользовательскую frontend-часть для домашнего задания 3.

## Что изменено после проверки HW2

Backend больше не держит всю логику в одном `server.py` и не использует `http.server`.

### Catalog service

Сервис каталога разделён на слои:

- `catalog/handlers.py` — HTTP-маршруты Flask;
- `catalog/services.py` — бизнес-логика каталога, валидация статусов и складских операций;
- `catalog/repositories.py` — SQL-запросы и преобразование записей БД в DTO;
- `catalog/database.py` — схема БД и seed-данные;
- `catalog/errors.py` — единый формат прикладных ошибок;
- `catalog/config.py` — настройки из environment variables.

### Order service

Сервис заказов также разделён на слои:

- `orders/handlers.py` — HTTP-маршруты Flask;
- `orders/services.py` — сценарии корзины и заказа;
- `orders/repositories.py` — работа с таблицами корзин, заказов и истории статусов;
- `orders/catalog_client.py` — отдельный клиент для HTTP-взаимодействия с catalog-service;
- `orders/database.py` — схема БД и seed-данные;
- `orders/errors.py` — единый формат ошибок;
- `orders/config.py` — настройки из environment variables.

Дополнительно добавлены:

- Flask вместо `http.server`;
- Gunicorn в Docker-контейнерах;
- централизованные error handlers;
- request logging middleware через `before_request` / `after_request`;
- единый JSON-ответ для ошибок;
- более явная валидация входных данных.

## Что реализовано для HW3

В папке `frontend/` находится React-приложение на Vite:

- каталог товаров;
- карточка товара;
- корзина;
- оформление заказа;
- подтверждение заказа;
- маршрутизация через React Router DOM;
- mock-данные без обязательного backend;
- адаптивная верстка для экранов от 320px;
- хранение корзины в `localStorage`.

## Структура

```text
catalog-service/
  app.py
  catalog/
    handlers.py
    services.py
    repositories.py
    database.py
    errors.py
    config.py
    utils.py
order-service/
  app.py
  orders/
    handlers.py
    services.py
    repositories.py
    catalog_client.py
    database.py
    errors.py
    config.py
    utils.py
frontend/
  src/
    components/
    context/
    data/
    pages/
    styles/
    utils/
```

## Запуск всего проекта через Docker Compose

```bash
docker compose up --build
```

После запуска:

- frontend: `http://localhost:5173`;
- catalog-service: `http://localhost:8081`;
- order-service: `http://localhost:8082`.

Проверка health endpoints:

```bash
curl http://localhost:8081/health
curl http://localhost:8082/health
```

## Локальный запуск frontend

```bash
cd frontend
npm install
npm run dev
```

## Локальный запуск backend без Docker

Catalog service:

```bash
cd catalog-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Order service:

```bash
cd order-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Для локального запуска order-service по умолчанию ожидает catalog-service на `http://localhost:8081`.
