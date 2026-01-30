# SaaS Unit Economics Dashboard

Инструмент для расчёта unit-экономики и финансового планирования SaaS-стартапов. Проект реализован как приложение Streamlit и объединяет хранение данных в SQLite, расчёт метрик по стадиям, планирование на 12 месяцев, сравнение с бенчмарками и генерацию отчётов.

## Возможности
- **Дашборд unit-экономики**: интерактивные графики, ключевые метрики, сравнение с целевыми значениями по стадии стартапа. 
- **Финансовое планирование на 12 месяцев**: прогноз MRR, расходов, CAC, cashflow, runway и др. 
- **Сценарии и анализ отклонений**: сравнение план/факт, чувствительность к допущениям. 
- **AI-рекомендации**: интеграция с GigaChat для аналитики и рекомендаций (опционально).
- **Экспорт отчётов**: investor deck, board report, monthly report, выгрузки в Excel/PDF/Word.

## Быстрый старт

### 1. Установка зависимостей
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Запуск приложения
```bash
streamlit run app.py
```

По умолчанию данные хранятся в SQLite базе `database/saas_finance.db`. База создаётся автоматически при запуске, но её также можно инициализировать вручную:
```bash
python database/init_db.py
```

## Конфигурация GigaChat (опционально)
Чтобы включить AI-аналитику, задайте переменные окружения:
```bash
export GIGACHAT_CLIENT_ID="..."
export GIGACHAT_CLIENT_SECRET="..."
export GIGACHAT_SCOPE="GIGACHAT_API_PERS"
export GIGACHAT_BASE_URL="https://gigachat.devices.sberbank.ru/api/v1"
export GIGACHAT_AUTH_URL="https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
export GIGACHAT_VERIFY_SSL="false"  # true/false
```
Сертификаты Сбера уже присутствуют в репозитории (`*.cer`, `*.pem`) и используются при работе с API.

## Структура проекта
```
.
├── app.py                       # Streamlit приложение
├── database/                    # SQLite и менеджер БД
│   ├── db_manager.py
│   ├── init_db.py
│   └── saas_finance.db
├── services/
│   ├── core/                    # Логика метрик, когорт, runway
│   ├── financial_system/        # Планирование, сценарии, бенчмарки
│   └── utils/                   # Валидация, экспорт, визуализация
├── reports/                     # Генерация отчётов
├── gigachat_analyst.py          # Интеграция с GigaChat
├── requirements.txt
└── tests/ (test_*.py)
```

## Основные модули
- **`app.py`** — точка входа, UI и оркестрация сервисов. 
- **`database/db_manager.py`** — модели и взаимодействие с SQLite. 
- **`services/core/`** — метрики по стадиям, когортный анализ, расчёт runway. 
- **`services/financial_system/`** — финансовые планы, сценарии, анализ отклонений, бенчмарки. 
- **`services/utils/`** — валидация данных, экспорты, визуализации. 
- **`reports/`** — генерация investor/board/monthly отчётов. 
- **`gigachat_analyst.py`** — AI-аналитик на базе GigaChat.

## Тесты
В репозитории есть базовые тесты (например, `test_company.py`, `test_database.py`). Их можно запускать через `pytest`:
```bash
pytest
```

## Примечания
- Проект ориентирован на SaaS-стартапы и предполагает работу с метриками MRR, churn, CAC, LTV, gross margin и runway.
- Основной интерфейс и отчёты рассчитаны на русский язык (метрики и описания).
