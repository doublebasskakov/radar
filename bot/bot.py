#!/usr/bin/env python3
"""
Telegram-бот с дайджестом. Работает без сервера — его запускает GitHub Actions каждые 15 минут.

  python bot/bot.py poll     # ответить на новые сообщения (/start, выбор города, /week, /stop)
  python bot/bot.py digest   # разослать еженедельный дайджест подписчикам (+ в канал, если задан)

Переменные окружения (секреты GitHub):
  TELEGRAM_BOT_TOKEN — токен от @BotFather
  BOT_STORE_KEY      — ключ шифрования списка подписчиков (создаётся командой: python bot/bot.py genkey)
  SITE_URL           — адрес сайта, напр. https://username.github.io/afisha-art/
  TELEGRAM_CHANNEL   — (необязательно) @канал, куда публиковать дайджест
"""
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "site" / "data" / "events.json"
STATE = ROOT / "data" / "bot_state.json"
SUBS = ROOT / "data" / "subscribers.enc"
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
SITE = os.environ.get("SITE_URL", "").rstrip("/") + "/"
API = f"https://api.telegram.org/bot{TOKEN}/"
TODAY = dt.datetime.now(ZoneInfo("Europe/Moscow")).date()
WORLD = "🌍 Только мир"
ALL = "🇷🇺 Все города"
OWNER = os.environ.get("OWNER_CHAT_ID", "")
STATE_ROBOT = ROOT / "data" / "state.json"
SOURCES = ROOT / "scraper" / "sources.yaml"


def tg(method, **params):
    r = requests.post(API + method, json=params, timeout=30)
    data = r.json()
    if not data.get("ok"):
        print("telegram:", method, data.get("description"))
    return data.get("result")


# ---------------------------------------------------------------- encrypted subscribers
def fernet():
    from cryptography.fernet import Fernet
    return Fernet(os.environ["BOT_STORE_KEY"].encode())


def load_subs():
    if not SUBS.exists():
        return {}
    return json.loads(fernet().decrypt(SUBS.read_bytes()).decode())


def save_subs(subs):
    SUBS.parent.mkdir(parents=True, exist_ok=True)
    SUBS.write_bytes(fernet().encrypt(json.dumps(subs, ensure_ascii=False).encode()))


def load_events():
    return json.loads(EVENTS.read_text(encoding="utf-8"))["events"]


def pdate(s):
    try:
        return dt.date.fromisoformat(s) if s and len(s) == 10 else None
    except ValueError:
        return None


# ---------------------------------------------------------------- digest
def week_events(events, city=None, region="ru", limit=10):
    end = TODAY + dt.timedelta(days=7)
    out = []
    for e in events:
        if (e.get("region") or "ru") != region or e.get("tba"):
            continue
        if city and e.get("city") != city:
            continue
        s, en = pdate(e.get("start")), pdate(e.get("end"))
        s = s or TODAY
        en = en or s
        opens = TODAY <= s <= end                         # начинается на этой неделе
        closing = s < TODAY and TODAY <= en <= end        # последние дни
        if opens or closing:
            out.append((-(e.get("importance") or 3), s, e, closing))
    out.sort(key=lambda x: (x[0], x[1]))
    return [(e, closing) for _, _, e, closing in out[:limit]]


def fmt_date(e):
    mon = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    s, en = pdate(e.get("start")), pdate(e.get("end"))
    if s and (not en or en == s):
        return f"{s.day} {mon[s.month-1]}" + (f", {e['time']}" if e.get("time") else "")
    if s and en:
        return f"{s.day} {mon[s.month-1]} — {en.day} {mon[en.month-1]}"
    return f"до {en.day} {mon[en.month-1]}" if en else ""


def line(e, closing=False):
    link = f"{SITE}#e={e['id']}" if SITE != "/" else e["src"]
    tail = " · <i>последние дни</i>" if closing else ""
    city = f" · {html.escape(e.get('city',''))}" if e.get("region") == "world" else ""
    return f"• <a href=\"{link}\">{html.escape(e['title'])}</a> — {html.escape(fmt_date(e))}, {html.escape(e.get('venue') or '')}{city}{tail}"


def digest_text(events, city):
    parts = []
    if city == ALL:
        rows = week_events(events, None, limit=12)
        parts.append("<b>Неделя: вся Россия</b>")
        parts += [line(e, c) + f" · {html.escape(e.get('city',''))}" for e, c in rows] or ["Пока пусто."]
    elif city and city != WORLD:
        rows = week_events(events, city)
        parts.append(f"<b>Неделя в городе {html.escape(city)}</b>")
        parts += [line(e, c) for e, c in rows] or ["На этой неделе в афише пусто — загляните на сайт."]
    world = week_events(events, region="world", limit=4)
    if world:
        parts.append("\n<b>В мире</b>")
        parts += [line(e, c) for e, c in world]
    if SITE != "/":
        parts.append(f"\n<a href=\"{SITE}\">Вся афиша →</a>")
    return "\n".join(parts)


def cities(events, n=12):
    cnt = {}
    for e in events:
        if (e.get("region") or "ru") == "ru":
            cnt[e["city"]] = cnt.get(e["city"], 0) + 1
    top = sorted(cnt, key=lambda c: (c != "Москва", -cnt[c]))[:n]
    return top


def city_keyboard(events):
    rows, row = [], []
    for c in [ALL] + cities(events) + [WORLD]:
        row.append({"text": c, "callback_data": "city:" + c[:50]})
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return {"inline_keyboard": rows}


# ---------------------------------------------------------------- commands
def poll():
    state = json.loads(STATE.read_text()) if STATE.exists() else {"offset": 0}
    upd = tg("getUpdates", offset=state["offset"], timeout=0, allowed_updates=["message", "callback_query"]) or []
    me = tg("getMe") or {}
    hook = tg("getWebhookInfo") or {}
    print(f"бот @{me.get('username')}: новых сообщений {len(upd)}, webhook={hook.get('url') or 'нет'}", flush=True)
    if not upd and state.get("menu"):
        return
    subs, events, changed = load_subs(), load_events(), False
    if SITE != "/" and not state.get("menu"):
        # кнопка «Радар» слева от поля ввода — открывает мини-приложение
        if tg("setChatMenuButton", menu_button={"type": "web_app", "text": "Радар", "web_app": {"url": SITE + "?tg=1"}}):
            state["menu"] = True
        tg("setMyCommands", commands=[{"command": "start", "description": "Открыть Радар"},
                                      {"command": "city", "description": "Город для дайджеста"},
                                      {"command": "week", "description": "Дайджест сейчас"},
                                      {"command": "stop", "description": "Отписаться"}])
    for u in upd:
        state["offset"] = u["update_id"] + 1
        if "callback_query" in u:
            q = u["callback_query"]; chat = str(q["message"]["chat"]["id"])
            data = q.get("data", "")
            if data.startswith(("src+:", "src-:")) and OWNER and chat == OWNER:
                u = data[5:]
                handle_candidate(u, data.startswith("src+:"))
                tg("answerCallbackQuery", callback_query_id=q["id"], text="Добавлено" if data.startswith("src+:") else "Отклонено")
                tg("editMessageReplyMarkup", chat_id=chat, message_id=q["message"]["message_id"], reply_markup={"inline_keyboard": []})
                continue
            if data.startswith("city:"):
                city = q["data"][5:]
                subs[chat] = {"city": city}; changed = True
                tg("answerCallbackQuery", callback_query_id=q["id"], text="Готово!")
                tg("sendMessage", chat_id=chat, parse_mode="HTML", disable_web_page_preview=True,
                   text=f"Подписка оформлена: <b>{html.escape(city)}</b>. Дайджест приходит по понедельникам.\n\n" + digest_text(events, city))
            continue
        m = u.get("message") or {}
        chat, text = str(m.get("chat", {}).get("id", "")), (m.get("text") or "").strip()
        if not chat:
            continue
        if text.startswith("/start suggest") or text.startswith("/suggest"):
            body = text.split(" ", 1)[1] if text.startswith("/suggest ") else ""
            if body and OWNER:
                who = m.get("from", {}).get("username") or m.get("from", {}).get("first_name", "")
                tg("sendMessage", chat_id=OWNER, text=f"Предложение от {who}:\n{body}")
                tg("sendMessage", chat_id=chat, text="Спасибо! Передал редакции.")
            else:
                tg("sendMessage", chat_id=chat, text="Пришлите одним сообщением: /suggest и ссылку на событие или канал (и пару слов о нём).")
        elif text.startswith("/start") or text.startswith("/city"):
            if SITE != "/":
                tg("sendMessage", chat_id=chat, text="Привет! Это «Радар» — афиша современного искусства: новая музыка, медиа-арт, выставки, кино, перформанс и театр.\n\nОткройте приложение — выберите город и листайте события:",
                   reply_markup={"inline_keyboard": [[{"text": "📍 Открыть Радар", "web_app": {"url": SITE + "?tg=1"}}]]})
            tg("sendMessage", chat_id=chat, text="А ещё могу присылать дайджест по понедельникам. Выберите город:", reply_markup=city_keyboard(events))
        elif text.startswith("/week"):
            city = subs.get(chat, {}).get("city")
            tg("sendMessage", chat_id=chat, parse_mode="HTML", disable_web_page_preview=True, text=digest_text(events, city) if city else "Сначала выберите город: /city")
        elif text.startswith("/myid"):
            tg("sendMessage", chat_id=chat, text=f"Ваш chat id: {chat}\nВпишите его в секрет OWNER_CHAT_ID, чтобы получать кандидатов в новые источники.")
        elif text.startswith("/stop"):
            if subs.pop(chat, None) is not None:
                changed = True
            tg("sendMessage", chat_id=chat, text="Вы отписались. Вернуться — /start")
        else:
            tg("sendMessage", chat_id=chat, text="Команды: /city — выбрать город, /week — дайджест сейчас, /stop — отписаться" + (f"\nСайт: {SITE}" if SITE != "/" else ""))
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state))
    if changed:
        save_subs(subs)


def handle_candidate(u, add):
    st = json.loads(STATE_ROBOT.read_text(encoding="utf-8")) if STATE_ROBOT.exists() else {}
    st.setdefault("candidates", {}).pop(u, None)
    if add:
        txt = SOURCES.read_text(encoding="utf-8")
        if f"u: {u}," not in txt:
            txt = txt.replace("\npages:", f"\n  - {{u: {u}, region: ru}}  # добавлен через бота\n\npages:", 1)
            SOURCES.write_text(txt, encoding="utf-8")
    else:
        st.setdefault("rejected", []).append(u)
    STATE_ROBOT.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def candidates():
    """Раз в неделю: владельцу — каналы, которые чаще всего упоминают и репостят наши источники."""
    if not OWNER or not STATE_ROBOT.exists():
        return
    st = json.loads(STATE_ROBOT.read_text(encoding="utf-8"))
    top = sorted(((n, u) for u, n in st.get("candidates", {}).items() if n >= 2), reverse=True)[:10]
    if not top:
        return
    tg("sendMessage", chat_id=OWNER, text="Кандидаты в новые источники за неделю (чаще всего упоминаются и репостятся):")
    for n, u in top:
        tg("sendMessage", chat_id=OWNER, text=f"https://t.me/s/{u}\nупоминаний: {n}",
           reply_markup={"inline_keyboard": [[{"text": "✅ Добавить", "callback_data": f"src+:{u}"[:64]},
                                              {"text": "✖ Нет", "callback_data": f"src-:{u}"[:64]}]]})


def digest():
    events, subs = load_events(), load_subs()
    for chat, s in subs.items():
        res = tg("sendMessage", chat_id=chat, parse_mode="HTML", disable_web_page_preview=True,
                 text="<b>Дайджест недели</b>\n\n" + digest_text(events, s.get("city")))
        if res is None:
            pass
    ch = os.environ.get("TELEGRAM_CHANNEL")
    if ch:
        parts = ["<b>Главное на неделе</b>"]
        for c in cities(events, 6):
            rows = week_events(events, c, limit=4)
            if rows:
                parts.append(f"\n<b>{html.escape(c)}</b>")
                parts += [line(e, cl) for e, cl in rows]
        world = week_events(events, region="world", limit=5)
        if world:
            parts.append("\n<b>В мире</b>"); parts += [line(e, cl) for e, cl in world]
        if SITE != "/":
            parts.append(f"\n<a href=\"{SITE}\">Вся афиша →</a>")
        tg("sendMessage", chat_id=ch, parse_mode="HTML", disable_web_page_preview=True, text="\n".join(parts)[:4000])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "poll"
    if cmd == "genkey":
        from cryptography.fernet import Fernet
        print(Fernet.generate_key().decode())
    elif not TOKEN:
        print("TELEGRAM_BOT_TOKEN не задан — бот пропущен")
    elif cmd == "poll":
        poll()
    elif cmd == "digest":
        digest()
        candidates()
