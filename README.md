# Радар — афиша современного искусства

Публичное веб-приложение: новая музыка, медиа- и диджитал-арт, выставки, перформанс, театр, ярмарки и биеннале — **в России** (все города) и **в мире**.

- Открывается по ссылке на любом устройстве; на iPhone/Android ставится на экран «Домой» и работает офлайн.
- Каждый день само собирает события из публичных Telegram-каналов, сайтов площадок, подборок и RSS.
- Кнопки «Apple Календарь» и «Google» у каждого события, подписки на календарь по городу/стране/жанру, избранное, RU/EN.
- Telegram-бот с еженедельным дайджестом по выбранному городу.

## Как это устроено

```
site/                 сайт (GitHub Pages): index.html, app.js, app.css, sw.js, manifest
  data/events.json    данные для сайта (генерируется)
  ics/, cal/          календари: по событию и подписки (генерируются)
  img/                картинки из афиш (скачиваются роботом)
scraper/robot.py      робот: collect (сбор + языковая модель) и build (сайт, календари, картинки)
scraper/sources.yaml  список источников — Telegram-каналы, сайты, RSS
data/events.json      основная база событий
data/editor.yaml      ручная редактура: закрепить / скрыть / добавить событие
bot/bot.py            Telegram-бот (опрос каждые 15 минут, дайджест по понедельникам)
.github/workflows/    расписание: update.yml (ежедневно), bot.yml (бот)
```

## Настройка (один раз, ~10 минут)

1. **Pages.** Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. **Ключ модели.** Settings → Secrets and variables → Actions → *New repository secret*:
   `ANTHROPIC_API_KEY` = ключ с console.anthropic.com (расход — порядка 1–5 $ в месяц).
   Модель по умолчанию — `claude-haiku-5-5`; можно сменить переменной `AFISHA_MODEL` (вкладка *Variables*).
3. **Первый запуск.** Actions → «Обновить афишу» → *Run workflow*. Через пару минут сайт будет на
   `https://<ваш-логин>.github.io/<имя-репозитория>/`.

### Telegram-бот (по желанию)

1. В Telegram напишите @BotFather → `/newbot` → получите токен.
2. Secrets: `TELEGRAM_BOT_TOKEN` = токен; `BOT_STORE_KEY` = ключ шифрования подписчиков
   (сгенерировать: `python bot/bot.py genkey` или любой Fernet-ключ).
3. Variables: `BOT_ENABLED` = `true`; по желанию `TELEGRAM_CHANNEL` = `@ваш_канал` (бот должен быть админом канала).
4. В `site/config.js` впишите `bot: "имя_бота"` — на сайте появится кнопка бота.

Список подписчиков хранится в репозитории **в зашифрованном виде** (`data/subscribers.enc`).

## Редактура

- `data/editor.yaml` → `pin:` — закрепить в «Выборе редакции», `hide:` — скрыть, `events:` — добавить вручную.
  id события виден в адресе карточки (`#e=<id>`).
- `scraper/sources.yaml` — добавляйте любые публичные Telegram-каналы и сайты.
- Правки можно делать прямо в веб-интерфейсе GitHub (значок карандаша) — сайт пересоберётся сам.

## Локальный запуск

```bash
pip install -r requirements.txt
AFISHA_IMAGES=0 python scraper/robot.py build
cd site && python -m http.server 8000   # http://localhost:8000
```
