#!/usr/bin/env python3
"""
Робот «Афиши современного искусства».

  python scraper/robot.py collect   # читает Telegram-каналы, сайты, RSS → новые события (нужен ANTHROPIC_API_KEY)
  python scraper/robot.py build     # собирает сайт: site/data/*.json, календари .ics, картинки
  python scraper/robot.py all       # collect + build

Работает в GitHub Actions по расписанию, Claude для работы не нужен.
"""
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
EVENTS_FILE = DATA / "events.json"
STATE_FILE = DATA / "state.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; AfishaArtBot/1.0; +https://github.com)"}
MODEL = os.environ.get("AFISHA_MODEL", "claude-haiku-5-5")
TODAY = dt.date.fromisoformat(os.environ["AFISHA_TODAY"]) if os.environ.get("AFISHA_TODAY") else \
    dt.datetime.now(ZoneInfo("Europe/Moscow")).date()
CATS = ["music", "media", "gallery", "performance", "fair", "theatre", "biennial", "cinema", "lecture"]
LOOKBACK_DAYS = 21          # насколько старые посты ещё разбирать
MAX_POSTS_PER_RUN = 400     # предохранитель расходов на модель


# ---------------------------------------------------------------- utils
def load_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def slug(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    tr = str.maketrans("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                       "abvgdeejziyklmnoprstufhccss_y_eua")
    s = s.translate(tr)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or hashlib.md5((s or "x").encode()).hexdigest()[:8]


def norm_title(t):
    return re.sub(r"[^a-zа-я0-9]+", "", (t or "").lower().replace("ё", "е"))[:40]


def pdate(s):
    try:
        return dt.date.fromisoformat(s) if s and len(s) == 10 else None
    except ValueError:
        return None


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- collect: telegram
MENTION_RE = re.compile(r"(?:t\.me/|telegram\.me/|(?<![\w.])@)([A-Za-z][A-Za-z0-9_]{4,31})")
NOT_CHANNELS = {"joinchat", "share", "addstickers", "proxy", "iv", "s", "c", "boost", "addlist"}


def note_mentions(w, text, discovered):
    """Собирает упоминания и репосты других каналов — кандидаты в новые источники."""
    found = set(MENTION_RE.findall(text))
    fw = w.select_one(".tgme_widget_message_forwarded_from_name")
    if fw and fw.get("href"):
        m = re.search(r"t\.me/([A-Za-z][A-Za-z0-9_]{4,31})", fw["href"])
        if m:
            found.add(m.group(1))
    for a in w.select(".tgme_widget_message_text a[href]"):
        m = re.search(r"t\.me/([A-Za-z][A-Za-z0-9_]{4,31})(?:$|[/?])", a["href"])
        if m:
            found.add(m.group(1))
    for u in found:
        if u.lower() not in NOT_CHANNELS and not u.lower().endswith("bot"):
            discovered[u] = discovered.get(u, 0) + 1


def fetch_telegram(username, seen, discovered=None):
    """Посты публичного канала с t.me/s/<username> (последние ~20)."""
    url = f"https://t.me/s/{username}"
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    posts = []
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=LOOKBACK_DAYS)
    for w in soup.select(".tgme_widget_message"):
        pid = w.get("data-post")  # "username/123"
        if not pid:
            continue
        key = "tg:" + pid
        if key in seen:
            continue
        t = w.select_one(".tgme_widget_message_date time")
        when = dt.datetime.fromisoformat(t["datetime"]) if t and t.get("datetime") else None
        if when and when < since:
            continue
        txt_el = w.select_one(".tgme_widget_message_text")
        text = txt_el.get_text("\n", strip=True) if txt_el else ""
        if discovered is not None:
            note_mentions(w, text, discovered)
        if len(text) < 60:
            continue
        photo = None
        ph = w.select_one(".tgme_widget_message_photo_wrap")
        if ph and ph.get("style"):
            m = re.search(r"url\('([^']+)'\)", ph["style"])
            photo = m.group(1) if m else None
        posts.append({"key": key, "text": text[:2500], "date": when.date().isoformat() if when else None,
                      "url": f"https://t.me/{pid}", "img": photo,
                      "srcName": "Telegram @" + username})
    return posts


# ---------------------------------------------------------------- collect: pages & rss
def page_text(html, base):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        tag.decompose()
    links = []
    for a in soup.select("a[href]")[:400]:
        label = a.get_text(" ", strip=True)
        if 8 < len(label) < 140:
            links.append(f"[{label}]({urllib.parse.urljoin(base, a['href'])})")
    text = re.sub(r"\n\s*\n+", "\n", soup.get_text("\n", strip=True))
    return (text[:14000] + "\n\nСсылки:\n" + "\n".join(links[:150]))[:20000]


def fetch_page(src, state):
    r = requests.get(src["url"], headers=UA, timeout=40)
    r.raise_for_status()
    txt = page_text(r.text, src["url"])
    h = hashlib.sha1(txt.encode()).hexdigest()
    key = "page:" + src["url"]
    if state["pages"].get(key) == h:
        return []
    state["pages"][key] = h
    return [{"key": key, "text": txt, "date": TODAY.isoformat(), "url": src["url"], "img": None,
             "srcName": urllib.parse.urlparse(src["url"]).netloc.replace("www.", ""), "long": True}]


def fetch_rss(src, seen):
    import feedparser
    feed = feedparser.parse(requests.get(src["url"], headers=UA, timeout=40).content)
    out = []
    for e in feed.entries[:30]:
        key = "rss:" + (e.get("id") or e.get("link"))
        if key in seen:
            continue
        summ = BeautifulSoup(e.get("summary", ""), "html.parser").get_text(" ", strip=True)
        out.append({"key": key, "text": (e.get("title", "") + "\n" + summ)[:2500], "date": TODAY.isoformat(),
                    "url": e.get("link"), "img": None,
                    "srcName": urllib.parse.urlparse(src["url"]).netloc.replace("www.", "")})
    return out


# ---------------------------------------------------------------- extract with LLM
PROMPT = """Ты — редактор афиши современного искусства. Сегодня {today}.
Ниже — фрагменты (посты Telegram-каналов, страницы сайтов). Найди в них КОНКРЕТНЫЕ будущие или идущие события,
которые проходят не раньше {today}, по темам: новая/экспериментальная академическая музыка, саунд-арт,
электроакустика; медиа- и цифровое искусство, видеоарт, AV-перформансы, иммерсивные выставки; выставки
современного искусства в музеях, центрах и галереях; перформанс; ярмарки и фестивали искусства; биеннале;
современный и экспериментальный театр и танец; КИНО: артхаус-премьеры, кинофестивали, ретроспективы,
спецпоказы с обсуждением, пресс-показы, видеоарт и экспериментальное кино (массовый прокат — НЕТ);
ЛЕКЦИИ об искусстве, музыке, кино и культуре, кураторские и авторские экскурсии, артист-токи, дискуссии (cat "lecture");
ОНЛАЙН-лекции и трансляции тоже включай: city "Онлайн", city_en "Online", country "Онлайн", venue — платформа, tz "Europe/Moscow".
НЕ включай: многонедельные платные курсы, open call, конкурсы, вакансии, распродажи, классику без современной составляющей,
детские шоу, мюзиклы, поп-концерты, новости без даты, события в прошлом.
Регион по умолчанию: {region_hint}.

Правила:
- Только то, что прямо следует из текста: дата, место. Не выдумывай. Если дня нет, но есть месяц —
  start "YYYY-MM" и "tba": true. Год определи по контексту (ближайшее будущее относительно {today}).
- desc / desc_en — 1–2 предложения СВОИМИ словами (не копируй фразы источника).
- importance: 1–5 (5 — событие, о котором будут говорить: крупная институция, важный автор, премьера, биеннале).
- press: true, если это пресс-показ / показ для аккредитованных.
- src_index — номер фрагмента, откуда событие. url — прямая ссылка на событие, если есть в тексте, иначе null.
- Для событий за рубежом country — страна по-русски, city — город по-русски.

Верни ТОЛЬКО JSON-массив (может быть пустым []), элементы:
{{"title":"","title_en":"","who":"","cat":"music|media|gallery|performance|fair|theatre|biennial|cinema|lecture","press":false,
"country":"Россия","country_en":"Russia","city":"","city_en":"","venue":"","address":"",
"start":"YYYY-MM-DD","end":"YYYY-MM-DD|null","time":"HH:MM|null","tz":"IANA, напр. Europe/Moscow",
"tba":false,"desc":"","desc_en":"","importance":3,"src_index":0,"url":null}}

Фрагменты:
{chunks}
"""


GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
_gemini_dead = False


def _gemini_models(key):
    """Если указанная модель недоступна — берём самую свежую flash-модель из списка."""
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": key, "pageSize": 200}, timeout=60)
    names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
             if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m["name"]
             and not any(x in m["name"] for x in ("tts", "live", "image", "audio", "lite"))]
    return sorted(names, key=lambda n: [int(x) if x.isdigit() else x for x in re.findall(r"\d+|\D+", n)], reverse=True)


def gemini(prompt):
    global GEMINI_MODEL, _gemini_dead
    key = os.environ.get("GEMINI_API_KEY")
    if not key or _gemini_dead:
        raise RuntimeError("gemini off")
    for attempt in range(4):
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                          params={"key": key}, timeout=240,
                          json={"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                                "generationConfig": {"responseMimeType": "application/json"}})
        if r.status_code == 404 and attempt == 0:
            models = _gemini_models(key)
            if models:
                GEMINI_MODEL = models[0]; log("  gemini: модель →", GEMINI_MODEL); continue
        if r.status_code == 429:
            if attempt >= 2:
                _gemini_dead = True  # дневной лимит исчерпан — до конца запуска идём в Claude
                raise RuntimeError("gemini quota")
            time.sleep(30 * (attempt + 1)); continue
        if r.status_code >= 500:
            time.sleep(10); continue
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    raise RuntimeError("gemini failed")


def claude(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY не задан")
    for attempt in range(4):
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=180,
                          headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json={"model": MODEL, "max_tokens": 8000,
                                "messages": [{"role": "user", "content": prompt}]})
        if r.status_code in (429, 500, 502, 503, 529):
            time.sleep(10 * (attempt + 1)); continue
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])
    raise RuntimeError("claude недоступен")


def llm_text(prompt):
    """Основная модель — бесплатная Gemini, запасная — Claude."""
    errors = []
    for fn in (gemini, claude):
        try:
            return fn(prompt)
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")
    raise RuntimeError("; ".join(errors))


def call_llm(prompt):
    text = llm_text(prompt)
    m = re.search(r"\[.*\]", text, re.S)
    return json.loads(m.group(0)) if m else []


def extract(items, region):
    events = []
    batch, size = [], 0
    def flush():
        nonlocal batch, size
        if not batch:
            return
        chunks = "\n\n".join(f"### [{i}] {it['srcName']} · {it.get('date') or ''} · {it['url']}\n{it['text']}"
                             for i, it in enumerate(batch))
        hint = "Россия" if region == "ru" else "весь мир (кроме России)"
        try:
            res = call_llm(PROMPT.format(today=TODAY.isoformat(), region_hint=hint, chunks=chunks))
        except Exception as e:
            log("  ! LLM:", e)
            res = []
        for ev in res:
            i = ev.get("src_index")
            src = batch[i] if isinstance(i, int) and 0 <= i < len(batch) else batch[0]
            ev["src"] = ev.get("url") or src["url"]
            ev["srcName"] = src["srcName"]
            ev["tg"] = src["key"].startswith("tg:")
            ev["_img"] = src.get("img")
            ev["region"] = region
            events.append(ev)
        batch, size = [], 0
    for it in items:
        L = len(it["text"])
        if batch and (size + L > 24000 or len(batch) >= 14):
            flush()
        batch.append(it)
        size += L
    flush()
    return events


def valid(ev):
    if ev.get("cat") not in CATS or not ev.get("title") or not ev.get("city"):
        return False
    s, e = pdate(ev.get("start")), pdate(ev.get("end"))
    if ev.get("tba"):
        return bool(re.fullmatch(r"\d{4}-\d{2}", str(ev.get("start") or "")))
    if not s:
        return False
    last = e or s
    return last >= TODAY and s <= TODAY + dt.timedelta(days=400)


def merge(master, new):
    index = {(norm_title(e["title"]), e.get("city")): e for e in master}
    added = 0
    for ev in new:
        if not valid(ev):
            continue
        k = (norm_title(ev["title"]), ev.get("city"))
        if k in index:
            old = index[k]
            for f in ("end", "time", "address", "venue", "desc_en", "title_en", "who"):
                if not old.get(f) and ev.get(f):
                    old[f] = ev[f]
            if old.get("tba") and not ev.get("tba"):
                old["start"], old["tba"] = ev["start"], False
            old["importance"] = max(old.get("importance", 3), ev.get("importance", 3))
            if not old.get("_img") and ev.get("_img"):
                old["_img"] = ev["_img"]
            continue
        base = slug(ev.get("title_en") or ev["title"]) + "-" + slug(ev.get("city_en") or ev["city"])[:12]
        eid, n = base, 2
        while any(x["id"] == eid for x in master):
            eid, n = f"{base}-{n}", n + 1
        ev["id"] = eid
        ev["added"] = TODAY.isoformat()
        ev.pop("src_index", None); ev.pop("url", None)
        master.append(ev)
        index[k] = ev
        added += 1
    return added


def collect():
    cfg = yaml.safe_load((ROOT / "scraper" / "sources.yaml").read_text(encoding="utf-8"))
    state = load_json(STATE_FILE, {"seen": [], "pages": {}})
    seen = set(state["seen"])
    master = load_json(EVENTS_FILE, [])
    pool = {"ru": [], "world": []}
    discovered = {}
    known = {c["u"].lower() for c in cfg.get("telegram", [])}
    for ch in cfg.get("telegram", []):
        try:
            posts = fetch_telegram(ch["u"], seen, discovered)
            if ch.get("city"):
                for p in posts:
                    p["text"] = f"(Площадка из города {ch['city']})\n" + p["text"]
            pool[ch.get("region", "ru")] += posts
            log(f"tg @{ch['u']}: {len(posts)}")
        except Exception as e:
            log(f"tg @{ch['u']}: ошибка {e}")
        time.sleep(1.2)
    for src in cfg.get("pages", []):
        try:
            items = fetch_page(src, state)
            if src.get("city"):
                for p in items:
                    p["text"] = f"(Город площадки: {src['city']})\n" + p["text"]
            pool[src.get("region", "ru")] += items
            log(f"page {src['url']}: {'изменилась' if items else 'без изменений'}")
        except Exception as e:
            log(f"page {src['url']}: ошибка {e}")
    for src in cfg.get("rss", []):
        try:
            pool[src.get("region", "world")] += fetch_rss(src, seen)
        except Exception as e:
            log(f"rss {src['url']}: ошибка {e}")
    total = 0
    for region, items in pool.items():
        items = items[:MAX_POSTS_PER_RUN]
        log(f"→ {region}: {len(items)} фрагментов на разбор")
        found = extract(items, region)
        n = merge(master, found)
        total += n
        log(f"→ {region}: найдено {len(found)}, новых {n}")
        for it in items:
            if not it.get("long"):
                seen.add(it["key"])
    cand = state.setdefault("candidates", {})
    rejected = set(x.lower() for x in state.setdefault("rejected", []))
    for u, n in discovered.items():
        if u.lower() not in known and u.lower() not in rejected:
            cand[u] = cand.get(u, 0) + n
    translate_missing(master)
    state["seen"] = sorted(seen)[-20000:]
    save_json(STATE_FILE, state)
    save_json(EVENTS_FILE, master)
    log(f"Готово: новых событий {total}, всего {len(master)}")


# ---------------------------------------------------------------- images
def og_image(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        soup = BeautifulSoup(r.text, "html.parser")
        for sel in ['meta[property="og:image"]', 'meta[name="twitter:image"]']:
            m = soup.select_one(sel)
            if m and m.get("content"):
                return urllib.parse.urljoin(url, m["content"])
        ph = soup.select_one(".tgme_widget_message_photo_wrap")
        if ph and ph.get("style"):
            m = re.search(r"url\('([^']+)'\)", ph["style"])
            return m.group(1) if m else None
    except Exception:
        return None


def fetch_images(events):
    from PIL import Image
    out_dir = SITE / "img"
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = 80
    for ev in events:
        target = out_dir / f"{ev['id']}.jpg"
        if target.exists():
            ev["img"] = f"img/{ev['id']}.jpg"
            continue
        if ev.get("noimg") or budget <= 0:
            continue
        url = ev.get("_img") or og_image(ev["src"])
        budget -= 1
        if not url:
            ev["noimg"] = True
            continue
        try:
            r = requests.get(url, headers=UA, timeout=30)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            if im.width < 300:
                ev["noimg"] = True
                continue
            im.thumbnail((900, 900))
            im.save(target, "JPEG", quality=78, optimize=True, progressive=True)
            ev["img"] = f"img/{ev['id']}.jpg"
            ev["imgCredit"] = ev.get("srcName")
        except Exception:
            ev["noimg"] = True


# ---------------------------------------------------------------- calendars
def ics_escape(t):
    return (t or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics_fold(line):
    b = line.encode("utf-8"); parts = []
    while len(b) > 73:
        cut = 73
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        parts.append(b[:cut].decode()); b = b[cut:]
    parts.append(b.decode())
    return "\r\n ".join(parts)


def cal_plan(ev):
    """(summary, start, end, timed) или None."""
    if ev.get("tba"):
        return None
    s, e = pdate(ev.get("start")), pdate(ev.get("end"))
    if not s:
        return None
    if ev.get("time"):
        try:
            h, m = map(int, ev["time"].split(":"))
            tz = ZoneInfo(ev.get("tz") or "Europe/Moscow")
            st = dt.datetime(s.year, s.month, s.day, h, m, tzinfo=tz).astimezone(dt.timezone.utc)
            return ev["title"], st, st + dt.timedelta(hours=2), True
        except Exception:
            pass
    if not e or e == s:
        return ev["title"], s, s + dt.timedelta(days=1), False
    if (e - s).days <= 7:
        return ev["title"], s, e + dt.timedelta(days=1), False
    if s >= TODAY:
        return "Открытие: " + ev["title"], s, s + dt.timedelta(days=1), False
    return "Последний день: " + ev["title"], e, e + dt.timedelta(days=1), False


def vevent(ev, p, stamp, base_url):
    summary, st, en, timed = p
    f = (lambda t: t.strftime("%Y%m%dT%H%M00Z")) if timed else (lambda t: t.strftime("%Y%m%d"))
    pre = "" if timed else ";VALUE=DATE"
    loc = ", ".join(x for x in [ev.get("venue"), ev.get("address"), ev.get("city"), ev.get("country") if ev.get("region") == "world" else None] if x)
    desc = f"{ev.get('desc','')}\n{ev.get('who','')}\n{ev['src']}"
    lines = ["BEGIN:VEVENT", f"UID:{ev['id']}@afisha-art", f"DTSTAMP:{stamp}", f"DTSTART{pre}:{f(st)}",
             f"DTEND{pre}:{f(en)}", f"SUMMARY:{ics_escape(summary)}", f"LOCATION:{ics_escape(loc)}",
             f"DESCRIPTION:{ics_escape(desc)}", f"URL:{base_url}#e={ev['id']}" if base_url else f"URL:{ev['src']}",
             "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{ics_escape(summary)}", "TRIGGER:-P1D", "END:VALARM",
             "END:VEVENT"]
    return "\r\n".join(ics_fold(l) for l in lines)


def calendar(name, vevents):
    head = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Afisha Art//RU", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
            f"X-WR-CALNAME:{ics_escape(name)}", "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
            "X-PUBLISHED-TTL:PT12H"]
    return "\r\n".join(ics_fold(l) for l in head) + "\r\n" + "\r\n".join(vevents) + \
        ("\r\n" if vevents else "") + "END:VCALENDAR\r\n"


# ---------------------------------------------------------------- build
def editor_rules():
    """data/editor.yaml: pin — в «Выбор редакции», hide — скрыть, events — добавить вручную."""
    p = DATA / "editor.yaml"
    if not p.exists():
        return {"pin": [], "hide": [], "events": []}
    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {"pin": cfg.get("pin") or [], "hide": cfg.get("hide") or [], "events": cfg.get("events") or []}


TRANSLATE_PROMPT = """Translate these contemporary-art event fields from Russian to natural English.
Return ONLY a JSON object mapping id -> {{"title_en": "...", "desc_en": "...", "city_en": "...", "country_en": "..."}}.
Keep proper names (venues, artists) transliterated as they are commonly written in English.
{items}"""


def translate_missing(master, limit=120):
    todo = [e for e in master if not e.get("desc_en") or not e.get("title_en")][:limit]
    for i in range(0, len(todo), 25):
        chunk = todo[i:i + 25]
        items = json.dumps({e["id"]: {"title": e["title"], "desc": e.get("desc", ""), "city": e.get("city"),
                                      "country": e.get("country")} for e in chunk}, ensure_ascii=False)
        try:
            text = llm_text(TRANSLATE_PROMPT.format(items=items))
            res = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
            for e in chunk:
                for k, v in (res.get(e["id"]) or {}).items():
                    if v and not e.get(k):
                        e[k] = v
        except Exception as ex:
            log("  ! перевод:", ex)


def build():
    master = load_json(EVENTS_FILE, [])
    rules = editor_rules()
    for ev in rules["events"]:
        if ev.get("id") and not any(x["id"] == ev["id"] for x in master):
            ev.setdefault("region", "ru"); ev.setdefault("importance", 4)
            master.append(ev)
    hidden = set(rules["hide"])
    for ev in master:
        if ev["id"] in rules["pin"]:
            ev["importance"] = 5
    base_url = os.environ.get("SITE_URL", "")
    live = []
    for ev in master:
        if ev["id"] in hidden:
            continue
        last = pdate(ev.get("end")) or pdate(ev.get("start"))
        if ev.get("tba") or (last and last >= TODAY):
            live.append(ev)
    if os.environ.get("AFISHA_IMAGES", "1") == "1":
        fetch_images(live)
    save_json(EVENTS_FILE, master)  # запоминаем noimg/img

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (SITE / "ics").mkdir(parents=True, exist_ok=True)
    (SITE / "cal").mkdir(parents=True, exist_ok=True)
    groups = {}
    public = []
    for ev in live:
        pub = {k: v for k, v in ev.items() if not k.startswith("_") and k not in ("noimg", "added")}
        pub["isNew"] = (ev.get("added") or "") >= (TODAY - dt.timedelta(days=3)).isoformat()
        p = cal_plan(ev)
        if p:
            ve = vevent(ev, p, stamp, base_url)
            (SITE / "ics" / f"{ev['id']}.ics").write_text(calendar(ev["title"], [ve]), encoding="utf-8", newline="")
            pub["ics"] = f"ics/{ev['id']}.ics"
            pub["calSummary"] = p[0]
            summary, st, en, timed = p
            f = (lambda t: t.strftime("%Y%m%dT%H%M00Z")) if timed else (lambda t: t.strftime("%Y%m%d"))
            pub["gcal"] = "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(
                {"action": "TEMPLATE", "text": summary, "dates": f"{f(st)}/{f(en)}",
                 "details": f"{ev.get('desc','')}\n{ev['src']}",
                 "location": ", ".join(x for x in [ev.get("venue"), ev.get("city")] if x)})
            reg = ev.get("region", "ru")
            place = f"{reg}-city-{slug(ev.get('city_en') or ev['city'])}" if reg == "ru" else \
                f"{reg}-country-{slug(ev.get('country_en') or ev.get('country') or 'other')}"
            for g in (f"{reg}-all", f"{reg}-cat-{ev['cat']}", place):
                groups.setdefault(g, []).append(ve)
            if ev.get("importance", 3) >= 4:
                groups.setdefault(f"{reg}-picks", []).append(ve)
        public.append(pub)
    names = {"ru": "Радар — Россия", "world": "Радар — Мир / World"}
    feeds = []
    for g, ves in groups.items():
        reg = g.split("-")[0]
        (SITE / "cal" / f"{g}.ics").write_text(calendar(names[reg] + " · " + g.split("-", 1)[1], ves),
                                                encoding="utf-8", newline="")
        feeds.append(g)
    public.sort(key=lambda e: (e.get("start") or "9999"))
    save_json(SITE / "data" / "events.json",
              {"updated": TODAY.isoformat(), "generated": stamp, "count": len(public), "feeds": sorted(feeds),
               "events": public})
    log(f"build: {len(public)} событий, {len(feeds)} календарных лент")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("collect", "all"):
        collect()
    if cmd in ("build", "all"):
        build()
