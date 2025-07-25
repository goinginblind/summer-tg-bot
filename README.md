# ЭНергосБот

**Телеграм-бот на базе Retrieval-Augmented Generation (RAG)**  
Проект выполнен в рамках Летней школы «Интеллект» 2025 года.

## Описание

Этот бот реализует интеллектуального помощника для обслуживания физических и юридических лиц. Основные возможности:

- **RAG-ответы** на вопросы пользователя с обсчётом внутренней документации (`documents.docx`).
- **Классификация запросов** на пять категорий:
  1. Жалоба пользователя  
  2. Запрос данных личного кабинета  
  3. Изменение данных личного кабинета  
  4. Регуляторно-правовые вопросы  
  5. Запрос на соединение с оператором  
- **Интерактивные сценарии** для физических и юридических лиц (выбор лицевого счёта, его изменение).
- **Заглушка** для работы с персональными данными: просмотр и редактирование (ФИО, телефон, дата рождения, счета, задолженность).
- **Логирование** всех вопросов и ответов в базе PostgreSQL.
- **Миграции** схем БД управляются через Alembic (основная база и заглушка).
- Реализовано с помощью: `python-telegram-bot`, `SQLAlchemy`, `LangChain`, `FAISS`, OpenAI GPT-4o-mini.

---

## Установка

```bash
git clone https://github.com/goinginblind/summer-tg-bot.git
cd summer-tg-bot
python -m venv venv             # Рекомендуется Python 3.10+
source venv/bin/activate
pip install -r requirements.txt
```

---

## Настройка

1. Скопируйте пример файла окружения и заполните секреты:
   ```bash
   cp .env.example .env
   ```
2. Отредактируйте `.env`, указав:
   ```dotenv
   BOT_TOKEN=<токен вашего бота Telegram>
   OPENAI_KEY=<API-ключ OpenAI>
   DATABASE_URL=postgresql://user:pass@host:port/main_db
   MOCKED_DB_URL=postgresql://user:pass@host:port/mocked_db
   ```

---

## Миграции базы данных

Выполните миграции для основной БД и заглушки:

```bash
# Основная БД (пользователи и логи)
alembic -c alembic.ini upgrade head

# БД-заглушка (персональные данные)
alembic -c alembic_mocked.ini upgrade head
```

---

## Запуск бота

При первом запуске индекс FAISS будет собран из `documents.docx` и сохранён в папке `docs/`.  
В последующих запусках индекс загружается автоматически.

```bash
python main.py
```

При успешном запуске в консоли появится сообщение  
`Bot is running…`  
и бот начнёт работу.

---

## Структура проекта

```
.
├── alembic/                   # Миграции для основной БД
├── alembic_mocked/            # Миграции для БД-заглушки
├── bot/
│   ├── bot.py                 # Инициализация окружения, БД, RAG; запуск Telegram handlers
│   └── handlers.py            # Обработчики /start, inline-кнопки, сценарии, редактирование данных
├── database/
│   ├── models.py              # ORM-модели: User, UserLog
│   ├── mocked_models.py       # ORM-модели для данных-заглушек
│   ├── queries.py             # CRUD и логирование для основной БД
│   └── mocked_queries.py      # CRUD для данных-заглушек
├── rag/
│   └── rag.py                 # RAG-pipeline: загрузка документов, сплиттер, FAISS, prompt-менеджер
├── documents.docx             # Внутренние документы для RAG
├── main.py                    # Точка входа: запуск бота
├── requirements.txt           # Зависимости Python
├── alembic.ini                # Конфиг Alembic для основной БД
├── alembic_mocked.ini         # Конфиг Alembic для БД-заглушки
├── .gitignore
└── README.md                  # Этот файл
```

---

## Конфигурация

- `BOT_TOKEN` — токен Telegram Bot API  
- `OPENAI_KEY` — API-ключ OpenAI (эмбеддинги, классификация, чат)  
- `DATABASE_URL` — DSN SQLAlchemy для основной БД  
- `MOCKED_DB_URL` — DSN для БД-заглушки  

---

## Использование

1. Пользователь отправляет команду **/start** и выбирает “Физическое лицо” или “Юридическое лицо”.  
2. Задаёт вопрос — бот классифицирует запрос и формирует ответ на основании документов и персональных данных.  
3. По кнопкам “Изменить персональные данные” или “Изменить номер лица” можно редактировать данные.  
4. Ответы формируются в вежливом, нейтральном и профессиональном стиле на русском языке.

---

## Лицензия

MIT License.  
Подробности см. в файле [LICENSE](LICENSE).
