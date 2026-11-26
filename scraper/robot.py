#!/usr/bin/env python3
"""
Робот «Афиши современного искусства».

  python scraper/robot.py collect   # читает Telegram-каналы, сайты, RSS → новые события (нужен OPENROUTER_API_KEY)
  python scraper/robot.py build     # собирает сайт: site/data/*.json, календари .ics, картинки
  python scraper/robot.py all       # collect + build

Работает в GitHub Actions по расписанию, Claude для работы не нужен.
"""
import atexit
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
MODEL = "particle-ai/particle-1:free"
TODAY = dt.date.fromisoformat(os.environ["AFISHA_TODAY"]) if os.environ.get("AFISHA_TODAY") else \
    dt.datetime.now(ZoneInfo("Europe/Moscow")).date()
CATS = ["music", "soundart", "club", "media", "gallery", "performance", "fair", "theatre", "biennial", "cinema", "lecture"]
LOOKBACK_DAYS = 21          # насколько старые посты ещё разбирать
MAX_POSTS_PER_RUN = 1500    # предохранитель расходов на модель


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


_CLUB = re.compile(r"\b(dj|диджей|ди-джей|b2b|рейв|rave|техно|techno|хаус|deep house|tech house|house music|вечеринк|party|all night|"
                   r"dex\b|mutabor|мутабор|powerhouse|monasterio|монастерио|gazgolder|berghain|tresor|"
                   r"drum.?n.?bass|dnb|бас-музык|afterparty|афтепати|open air)", re.I)


_CLUB_NAMES = re.compile(r"sónar|sonar 20|berlin atonal|dekmantel|awakenings|dimensions festival|"
                         r"\brndm\b|зангези|\bритмы\b|monasterio|mutabor|мутабор|\bdex\b|powerhouse|gazgolder|"
                         r"diskonoir|disko|дискотек|техно-|techno", re.I)


_SOUNDART = re.compile(r"саунд-арт|sound ?art|звуков\w* (?:инсталляц|прогулк|искусств|объект)|полев\w* запис|field recording|"
                       r"deep listening|глубок\w* слушан|нойз|noise|дроун|drone|эмбиент|ambient|импровизац|improvis|"
                       r"шумов|плёночн|сонификац|soundartist|музей звука|f5 /|модульн\w* синтез", re.I)


def is_soundart(ev):
    if ev.get("cat") not in ("music", "media", "gallery", "performance", "lecture"):
        return False
    if ev.get("cat") == "music" and re.search(r"акусм|acousm|grm|ircam|ЦЭАМ|CEAM|ансамбл|ensemble|квартет|оркестр|"
                                               r"филармон|консерват", " ".join(str(ev.get(k) or "") for k in ("title", "who", "venue")), re.I):
        return False
    txt = " ".join(str(ev.get(k) or "") for k in ("title", "title_en", "who", "venue"))
    if ev.get("cat") in ("gallery", "media", "lecture"):     # там — только явный саунд-арт
        return bool(re.search(r"саунд-арт|sound ?art|звуков\w* (?:инсталляц|искусств)|soundartist|музей звука|психоакуст", txt, re.I))
    return bool(_SOUNDART.search(txt))


def is_club(ev):
    if _CLUB_NAMES.search(" ".join(str(ev.get(k) or "") for k in ("title", "venue", "who"))):
        return True
    if re.search(r"ambient|эмбиент|festival|фестиваль|лаборатор|лекци|книжн", ev.get("title") or "", re.I):
        return False
    txt = " ".join(str(ev.get(k) or "") for k in ("title", "title_en", "who", "venue"))
    return bool(_CLUB.search(txt))


_STOP = {"концерт", "концерта", "выставка", "выставки", "спектакль", "лекция", "фестиваль", "премьера", "встреча",
         "concert", "exhibition", "festival", "lecture", "performance", "премьеры", "программа", "вечер", "show"}


def _tokens(e):
    txt = " ".join(str(e.get(k) or "") for k in ("title", "title_en")).lower().replace("ё", "е")
    return {w[:7] for w in re.findall(r"[a-zа-я0-9]{4,}", txt) if w not in _STOP}


def _quoted(e):
    return {norm_title(q) for q in re.findall(r"[«\"“]([^»\"”]{4,})[»\"”]", e.get("title") or "") if len(norm_title(q)) >= 4}


def _names(e):
    txt = " ".join(str(e.get(k) or "") for k in ("title", "who"))
    return {w.lower()[:7] for w in re.findall(r"\b[А-ЯЁA-Z][а-яёa-z]{4,}", txt)} - {w[:7] for w in _STOP}


_CHILD = re.compile(r"стенд|на ярмарке|на стенде|\bна\s+[A-ZА-ЯЁ|«]|в рамках|\bat\s+[A-Z]", re.I)
_SERIES = re.compile(r"цикл|серия|паблик-токи|программа|фестивал|конференц|festival|series", re.I)


def _multi(e):
    s0, e0 = pdate(e.get("start")), pdate(e.get("end"))
    return bool(s0 and e0 and e0 > s0)


def part_of(child, parent):
    """child — отдельное событие внутри parent (стенд на ярмарке, концерт фестиваля, встреча цикла)."""
    if child.get("festival") and norm_title(child["festival"])[:12] in norm_title(parent.get("title")):
        return True
    if _CHILD.search(child.get("title") or "") and not _CHILD.search(parent.get("title") or ""):
        return True
    return bool(_SERIES.search(parent.get("title") or "") and not _SERIES.search(child.get("title") or "")
                and not _multi(child))


def same_event(a, b):
    """Одно ли это событие: тот же город и день, похожие названия или те же участники."""
    if (a.get("city") or "") != (b.get("city") or ""):
        return False
    sa, sb = a.get("start") or "", b.get("start") or ""
    if sa != sb and not ((a.get("tba") or b.get("tba")) and sa[:7] == sb[:7]):
        return False
    ta, tb = a.get("time"), b.get("time")
    if ta and tb and ta != tb:
        return False
    if a.get("festival") and b.get("festival") and a.get("venue") and b.get("venue") and a["venue"] != b["venue"]:
        return False
    if _quoted(a) & _quoted(b) and not (_CHILD.search(a.get("title") or "") or _CHILD.search(b.get("title") or "")):
        return True
    if part_of(a, b) or part_of(b, a):
        return False
    na, nb = norm_title(a.get("title")), norm_title(b.get("title"))
    if na == nb or (min(len(na), len(nb)) >= 8 and (na in nb or nb in na)):
        return True
    if _quoted(a) & _quoted(b):
        return True
    A, B = _tokens(a), _tokens(b)
    if A and B and len(A & B) / len(A | B) >= 0.5:
        return True
    return len(_names(a) & _names(b)) >= 2 and len(A & B) >= 1


def _quality(e):
    return (bool(e.get("time")), not e.get("tba"), bool(e.get("img") or e.get("_img")),
            e.get("importance", 3), len(e.get("desc") or ""))


def dedupe(master):
    """Сливает дубликаты: оставляет лучшую карточку, дописывает в неё недостающие поля."""
    out, removed = [], 0
    for e in sorted(master, key=_quality, reverse=True):
        twin = next((k for k in out if same_event(k, e)), None)
        if twin is None:
            out.append(e)
            continue
        for f in ("end", "time", "address", "venue", "desc_en", "title_en", "who", "festival", "img", "imgCredit", "_img"):
            if not twin.get(f) and e.get(f):
                twin[f] = e[f]
        twin["importance"] = max(twin.get("importance", 3), e.get("importance", 3))
        twin.setdefault("aliases", [])
        twin["aliases"] = sorted(set(twin["aliases"]) | {e["id"]} | set(e.get("aliases", [])))
        removed += 1
    master[:] = out
    return removed


def pdate(s):
    try:
        return dt.date.fromisoformat(s) if s and len(s) == 10 else None
    except (TypeError, ValueError):
        return None


_WELLNESS = re.compile(
    r"(?<!\w)(?:йог(?:а|и|е|у|ой|ою)?|(?:хатха|кундалини)[ -]?йог\w*|yoga|пилатес\w*|pilates|"
    r"цигун\w*|qigong|ретрит\w*|wellness|breathwork|звуковая ванна|sound bath)(?!\w)"
    r"|медитативн\w*\s+(?:вечер|практик\w*|сеанс\w*|заняти\w*)"
    r"|(?:сеанс|сессия|занятие|практика|групповая|звуковая|управляемая)\s+медитац\w*"
    r"|(?:guided|group|sound)\s+meditation\b|\bmeditation\s+(?:session|class|workshop|practice)\b"
    r"|дыхательн\w*\s+(?:практик\w*|гимнастик\w*)", re.I)
_MEDITATION_TITLE = re.compile(r"^\s*[«\"“]?\s*(?:медитаци[яию]|meditation)\s*(?:$|[»\"”:.]|с\s|with\s)", re.I)
_DATE_YEAR = re.compile(
    r"\b(?:((?:19|20)\d{2})[-/.]\d{1,2}(?:[-/.]\d{1,2})?"
    r"|\d{1,2}[./-]\d{1,2}[./-]((?:19|20)\d{2})"
    r"|(?:\d{1,2}\s+)?(?:январ\w*|феврал\w*|март\w*|апрел\w*|ма[йяе]|июн\w*|июл\w*|"
    r"август\w*|сентябр\w*|октябр\w*|ноябр\w*|декабр\w*|jan\w*|feb\w*|mar\w*|apr\w*|may|"
    r"jun\w*|jul\w*|aug\w*|sep\w*|oct\w*|nov\w*|dec\w*)(?:\.?\s+\d{1,2},?)?[\s,]+((?:19|20)\d{2}))\b", re.I)


def outside_scope(ev):
    titles = [str(ev.get(k) or "") for k in ("title", "title_en")]
    return any(_WELLNESS.search(title) or _MEDITATION_TITLE.search(title) for title in titles)


def event_dates(ev):
    """Return the first and last possible dates, including month-only announcements."""
    s, e = pdate(ev.get("start")), pdate(ev.get("end"))
    if ev.get("end") and not e:
        return None, None
    if ev.get("tba") and not s:
        month = ev.get("start") or ""
        if isinstance(month, str) and re.fullmatch(r"\d{4}-\d{2}", month):
            s = pdate(month + "-01")
            if s:
                next_month = (s.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
                return s, e or next_month - dt.timedelta(days=1)
    return s, e or s


def current_event(ev):
    s, last = event_dates(ev)
    if not s:
        return False
    horizon = TODAY + dt.timedelta(days=400)
    return s <= last and TODAY <= last <= horizon and s <= horizon


def source_confirms_date(ev, src):
    s, last = event_dates(ev)
    quote = ev.get("date_quote")
    if not s or not last or not isinstance(quote, str):
        return False
    quote = " ".join(quote.split()).casefold()
    if not quote or len(quote) > 240 or quote not in " ".join(src["text"].split()).casefold():
        return False
    years = {int(next(y for y in m.groups() if y)) for m in _DATE_YEAR.finditer(quote)}
    if years:
        if years == {s.year, last.year}:
            return True
        return years == {s.year} and last.year == s.year + 1 and s.month == 12 and last.month == 1
    if not _DATE_HINT.search(quote) and not ev.get("tba"):
        return False
    posted = pdate(src.get("date"))
    base = posted or TODAY
    if s.year == base.year:
        return not posted or last >= posted
    return bool(posted and posted.month >= 11 and s.month <= 2 and s.year == posted.year + 1)


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
    return [{"key": key, "text": txt, "date": None, "url": src["url"], "img": None,
             "srcName": urllib.parse.urlparse(src["url"]).netloc.replace("www.", ""), "long": True}]


def fetch_rss(src, seen):
    import feedparser
    feed = feedparser.parse(requests.get(src["url"], headers=UA, timeout=40).content)
    out = []
    for e in feed.entries[:30]:
        key = "rss:" + (e.get("id") or e.get("link"))
        if key in seen:
            continue
        timestamp = e.get("published_parsed") or e.get("updated_parsed")
        published = dt.date(*timestamp[:3]) if timestamp else None
        if published and published < TODAY - dt.timedelta(days=LOOKBACK_DAYS):
            continue
        summ = BeautifulSoup(e.get("summary", ""), "html.parser").get_text(" ", strip=True)
        out.append({"key": key, "text": (e.get("title", "") + "\n" + summ)[:2500], "date": published.isoformat() if published else None,
                    "url": e.get("link"), "img": None,
                    "srcName": urllib.parse.urlparse(src["url"]).netloc.replace("www.", "")})
    return out


# ---------------------------------------------------------------- extract with LLM
PROMPT = """Ты — редактор афиши современного искусства. Сегодня {today}.
Ниже — фрагменты (посты Telegram-каналов, страницы сайтов). Найди в них КОНКРЕТНЫЕ будущие или идущие события,
которые проходят не раньше {today}, по темам: новая/экспериментальная академическая музыка, саунд-арт,
электроакустика (ОСОБЫЙ ПРИОРИТЕТ: акусматика, live electronics, мультимедийные концерты, концерты на акусмониуме,
выставки электромузыкальных инструментов и звуковых объектов — ЦЭАМ, IRCAM, INA GRM, Термен-центр и т.п.); САУНД-АРТ — отдельная рубрика cat "soundart": выставки и инсталляции звукового искусства, звуковые прогулки,
полевые записи, deep listening, экспериментальные концерты (нойз, дроун, эмбиент, свободная импровизация,
модульные синтезаторы, плёночные петли, DIY-инструменты, многоканальный звук), саунд-арт-мероприятия и лекции о
звуке в галереях и пространствах вроде soundartist.ru, Музея звука, F5, Московской шумовой мануфактуры;
cat "music" — композиторская новая/академическая музыка, ансамбли новой музыки, электроакустика и акусматика;
ЭЛЕКТРОННАЯ ТАНЦЕВАЛЬНАЯ И КЛУБНАЯ МУЗЫКА — отдельная рубрика cat "club": вечеринки и рейвы, DJ-сеты, техно, хаус,
электро, бас-музыка, клубные ночи (DEX, Mutabor, Powerhouse, Monasterio, Berghain и т.п.), танцевальные фестивали;
МУЛЬТИМЕДИА-ИНСТАЛЛЯЦИИ, световые и звуковые инсталляции, проекционные шоу, медиафасады (cat "media");
ФЕСТИВАЛИ электронной музыки, медиаискусства, новых технологий и искусства (CTM, Unsound, MUTEK, Ars Electronica,
Сигнал и т.п.) — с программой по отдельным событиям;
медиа- и цифровое искусство, видеоарт, AV-перформансы, иммерсивные выставки; выставки
современного искусства в музеях, центрах и галереях; перформанс; ярмарки и фестивали искусства; биеннале;
современный и экспериментальный театр и танец; КИНО: артхаус-премьеры, кинофестивали, ретроспективы,
спецпоказы с обсуждением, пресс-показы, видеоарт и экспериментальное кино (массовый прокат — НЕТ);
ЛЕКЦИИ об искусстве, музыке, кино и культуре, кураторские и авторские экскурсии, артист-токи, дискуссии (cat "lecture");
ОНЛАЙН-лекции и трансляции тоже включай: city "Онлайн", city_en "Online", country "Онлайн", venue — платформа, tz "Europe/Moscow".
НЕ включай: многонедельные платные курсы, open call, конкурсы, вакансии, распродажи, классику без современной составляющей,
детские шоу, мюзиклы, поп-, рок-, джаз-, блюз- и эстрадные концерты, премии и церемонии награждения, дискотеки с поп-музыкой и коммерческие вечеринки без DJ-лайнапа, новости без даты, события в прошлом. Исключай йогу, медитацию, ретриты, духовные и оздоровительные практики, даже если они проходят в музее или сопровождаются музыкой. Если это выставка, концерт или произведение искусства и «медитация» лишь образ в названии, включай. Любая активность без явной связи с заявленными видами искусства не подходит.
Регион по умолчанию: {region_hint}.

Правила:
- Только то, что прямо следует из текста: дата, место. Не выдумывай. Если дня нет, но есть месяц —
  start "YYYY-MM" и "tba": true. Сохраняй год даты из анонса. Если год опущен, используй год публикации, а при отсутствии даты публикации — текущий год. Январь или февраль следующего года возможны для датированных анонсов ноября или декабря, когда речь явно идёт о ближайших месяцах. Прошлый анонс никогда не переносится в следующий год только ради попадания в афишу. На архивных страницах пропускай события с неясным годом.
- date_quote: дословный фрагмент одного источника длиной до 240 символов с датой именно этого события (включая год и конец периода, если указаны). Не бери дату публикации, дату произведения или даты другой редакции фестиваля.
- desc / desc_en — 1–2 предложения СВОИМИ словами (не копируй фразы источника).
- importance: 1–5 (5 — событие, о котором будут говорить: крупная институция, важный автор, премьера, биеннале).
- press: true, если это пресс-показ / показ для аккредитованных.
- src_index — номер фрагмента, откуда событие. url — прямая ссылка на событие, если есть в тексте, иначе null.
- Для событий за рубежом country — страна по-русски, city — город по-русски.
- ФЕСТИВАЛИ, циклы, конференции, программы с несколькими днями или площадками: если в тексте есть программа —
  сделай ОТДЕЛЬНОЕ событие на каждый концерт / спектакль / показ / лекцию / выставку программы, со своей датой,
  временем и площадкой, и укажи в поле "festival" название фестиваля. Общую карточку фестиваля в этом случае НЕ делай.
  Только если программы в тексте нет — одна карточка фестиваля с датами начала и конца.
- Одно и то же событие из разных фрагментов верни ОДИН раз.

Верни ТОЛЬКО JSON-массив (может быть пустым []), элементы:
{{"title":"","title_en":"","who":"","cat":"music|soundart|club|media|gallery|performance|fair|theatre|biennial|cinema|lecture","press":false,
"country":"Россия","country_en":"Russia","city":"","city_en":"","venue":"","address":"",
"start":"YYYY-MM-DD","end":"YYYY-MM-DD|null","time":"HH:MM|null","tz":"IANA, напр. Europe/Moscow",
"tba":false,"festival":null,"desc":"","desc_en":"","importance":3,"src_index":0,"url":null,"date_quote":""}}

Фрагменты:
{chunks}
"""


CF_MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8-fast"
_cf_usage = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "unreported": 0}


def report_cf_usage():
    if not _cf_usage["requests"]:
        return
    neurons = (_cf_usage["prompt_tokens"] * 4119 + _cf_usage["completion_tokens"] * 34868) / 1_000_000
    summary = f"Workers AI: {_cf_usage}, оценка по учтённым токенам: {neurons:.1f} Neurons"
    log(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
            print(summary, file=output)


atexit.register(report_cf_usage)


def cloudflare_text(prompt):
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account) or not token:
        raise RuntimeError("Для Workers AI нужны CLOUDFLARE_ACCOUNT_ID и CLOUDFLARE_API_TOKEN")
    _cf_usage["requests"] += 1
    response = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{CF_MODEL}",
        headers={"Authorization": f"Bearer {token}"}, timeout=(10, 150),
        json={"messages": [{"role": "user", "content": prompt}], "max_tokens": 4096})
    response.raise_for_status()
    result = response.json()["result"]
    usage = result.get("usage") or {}
    if "prompt_tokens" in usage and "completion_tokens" in usage:
        for field in ("prompt_tokens", "completion_tokens"):
            _cf_usage[field] += usage[field]
    else:
        _cf_usage["unreported"] += 1
    text = result.get("response")
    if not text or not text.strip():
        raise RuntimeError("Cloudflare вернул пустой ответ")
    return text


def llm_text(prompt):
    if os.environ.get("RADAR_AI_PROVIDER") == "cloudflare":
        return cloudflare_text(prompt)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY не задан")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 8000}, timeout=(10, 150))
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("OpenRouter вернул пустой ответ")
    return text


def call_llm(prompt):
    text = llm_text(prompt)
    m = re.search(r"\[.*\]", text, re.S)
    return json.loads(m.group(0)) if m else []


LLM_DEADLINE = time.time() + int(os.environ.get("AFISHA_LLM_MINUTES", "70")) * 60


def extract(items, region, done=None):
    """done — множество ключей фрагментов, которые модель действительно разобрала."""
    events = []
    batch, size = [], 0
    def flush():
        nonlocal batch, size
        if not batch:
            return
        if time.time() > LLM_DEADLINE:
            log("  ! лимит времени на модель — остаток разберу в следующий запуск")
            batch, size = [], 0
            return
        chunks = "\n\n".join(f"### [{i}] {it['srcName']} · {it.get('date') or ''} · {it['url']}\n{it['text']}"
                             for i, it in enumerate(batch))
        hint = "Россия" if region == "ru" else "весь мир (кроме России)"
        try:
            res = call_llm(PROMPT.format(today=TODAY.isoformat(), region_hint=hint, chunks=chunks))
            if done is not None:
                done.update(it["key"] for it in batch)
        except Exception as e:
            log("  ! LLM:", e)
            res = []
        for ev in res:
            if not isinstance(ev, dict):
                continue
            i = ev.get("src_index")
            if not isinstance(i, int) or not 0 <= i < len(batch):
                continue
            src = batch[i]
            if not source_confirms_date(ev, src):
                continue
            ev.pop("date_quote", None)
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


def normalize_stage_city(ev):
    venue = " ".join(str(ev.get("venue") or "").casefold().split())
    src = urllib.parse.urlsplit(ev.get("src") or "")
    channel = (src.hostname in {"t.me", "telegram.me"} and
               re.match(r"^/(?:s/)?newstageprojects(?:/|$)", src.path, re.I))
    own_source = channel or ev.get("srcName", "") == "Telegram @newstageprojects" or src.hostname in {"alexandrinsky.ru", "www.alexandrinsky.ru"}
    new_stage = re.search(r"новая сцена|new stage", venue)
    if new_stage and (re.search(r"александрин|alexandrin|мейерхольд|meyerhold", venue) or
                      (own_source and venue in {"новая сцена", "new stage"})):
        ev.update(city="Санкт-Петербург", city_en="Saint Petersburg", region="ru", country="Россия", country_en="Russia", tz="Europe/Moscow")


def valid(ev):
    normalize_stage_city(ev)
    if ev.get("cat") == "music" and is_club(ev):
        ev["cat"] = "club"
    elif is_soundart(ev):
        ev["cat"] = "soundart"
    return bool(ev.get("cat") in CATS and ev.get("title") and ev.get("city")
                and not outside_scope(ev) and current_event(ev))


def merge(master, new):
    index = {(norm_title(e["title"]), e.get("city"), (e.get("start") or "")[:4]): e for e in master}
    added = 0
    for ev in new:
        if not valid(ev):
            continue
        k = (norm_title(ev["title"]), ev.get("city"), ev["start"][:4])
        old = index.get(k) or next((x for x in master if same_event(x, ev)), None)
        if old is not None:
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


_DATE_HINT = re.compile(
    r"\b\d{1,2}\s*(?:[-–—]\s*\d{1,2}\s*)?(?:янв|фев|мар|апр|мая|май|июн|июл|авг|сен|окт|ноя|дек|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"|\b\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?\b|\b\d{1,2}:\d{2}\b|сегодня|завтра|today|tonight|tomorrow"
    r"|понедельник|вторник|сред[ау]|четверг|пятниц|суббот|воскресень|monday|tuesday|wednesday|thursday|friday|saturday|sunday",
    re.I)


def fair_queue(groups):
    """Посты по очереди из каждого источника (а не первые N из первых каналов списка).
    Сначала — посты, где есть дата или время: в них почти всегда анонсы."""
    dated = [[p for p in g if p.get("long") or _DATE_HINT.search(p.get("text", ""))] for g in groups]
    out, i = [], 0
    while any(i < len(g) for g in dated):
        for g in dated:
            if i < len(g):
                out.append(g[i])
        i += 1
    return out


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
            pool[ch.get("region", "ru")].append(posts)
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
            pool[src.get("region", "ru")].append(items)
            log(f"page {src['url']}: {'изменилась' if items else 'без изменений'}")
        except Exception as e:
            log(f"page {src['url']}: ошибка {e}")
    for src in cfg.get("rss", []):
        try:
            pool[src.get("region", "world")].append(fetch_rss(src, seen))
        except Exception as e:
            log(f"rss {src['url']}: ошибка {e}")
    total = 0
    for region, groups in pool.items():
        items = fair_queue(groups)[:MAX_POSTS_PER_RUN]
        log(f"→ {region}: {len(items)} фрагментов на разбор")
        done = set()
        found = extract(items, region, done)
        n = merge(master, found)
        total += n
        log(f"→ {region}: разобрано {len(done)} из {len(items)}, найдено {len(found)}, новых {n}")
        for it in items:
            if it["key"] in done and not it.get("long"):
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
            title = ev["title"]
            if e and (e - s).days > 7:          # выставка с часами работы — в календарь идёт открытие
                title = "Открытие: " + title
            return title, st, st + dt.timedelta(hours=2), True
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


def calendar(name, vevents, feed=True):
    """feed=False — файл одного события: без имени календаря и интервала обновления,
    иначе iPhone предлагает «Подписаться» вместо «Добавить событие»."""
    head = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Afisha Art//RU", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    if feed:
        head += [f"X-WR-CALNAME:{ics_escape(name)}", "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
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


TIME_CATS = ("music", "soundart", "club", "theatre", "performance", "lecture", "cinema", "media")
TIMES_PROMPT = """Сегодня {today}. Для каждого события ниже найди только в приложенных источниках
ТОЧНОЕ время начала по местному времени. Сверь полную дату, включая год; совпадения с прошлогодними показами пропускай. Если показов несколько в разные дни — время первого показа и, если у
других дней время другое, перечисли их в "times" как {{"YYYY-MM-DD":"HH:MM"}}. Для выставок — время открытия
вернисажа в день открытия, если оно есть, иначе null. Не выдумывай: если не нашёл точно — "time": null.
Верни ТОЛЬКО JSON-объект вида {{"<id>": {{"time": "HH:MM"|null, "times": {{}}, "source": "url"}}}}.
События:
{items}"""


def source_material(events):
    config = yaml.safe_load((ROOT / "scraper" / "sources.yaml").read_text(encoding="utf-8"))
    hosts = {urllib.parse.urlsplit(s["url"]).hostname for kind in ("pages", "rss") for s in config.get(kind, [])}
    hosts.add("t.me")
    pages = []
    for url in dict.fromkeys(e.get("src") for e in events if e.get("src")):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.netloc != parsed.hostname:
            continue
        try:
            result = requests.get(url, headers=UA, timeout=12, allow_redirects=False)
            if result.status_code == 200:
                pages.append(url + "\n" + page_text(result.text, url)[:6000])
        except requests.RequestException:
            continue
    return "\n\n".join(pages)


def fill_times(master, limit=72):
    """Концертам, спектаклям, лекциям без времени ищем точное время начала (раз на событие)."""
    st = load_json(STATE_FILE, {"seen": [], "pages": {}})
    tried = set(st.get("time_tried", []))
    horizon = TODAY + dt.timedelta(days=90)
    todo = [e for e in master if not e.get("time") and e["id"] not in tried and not e.get("tba")
            and (e.get("cat") in TIME_CATS or (pdate(e.get("start")) or TODAY) >= TODAY)
            and TODAY <= (pdate(e.get("start")) or TODAY) <= horizon
            and not (e.get("cat") == "gallery" and (pdate(e.get("start")) or TODAY) < TODAY)]
    todo.sort(key=lambda e: (e.get("cat") not in TIME_CATS, e.get("start") or ""))
    todo = todo[:limit]
    n = 0
    for i in range(0, len(todo), 6):
        chunk = todo[i:i + 6]
        items = "\n".join(json.dumps({"id": e["id"], "title": e["title"], "who": e.get("who"), "venue": e.get("venue"),
                                      "city": e.get("city"), "start": e.get("start"), "end": e.get("end"),
                                      "src": e.get("src")}, ensure_ascii=False) for e in chunk)
        try:
            sources = source_material(chunk)
            if not sources:
                continue
            text = llm_text(TIMES_PROMPT.format(today=TODAY.isoformat(), items=items) + "\nИсточники:\n" + sources)
        except Exception as ex:
            log("  ! время:", ex)
            break
        m = re.search(r"\{.*\}", text, re.S)
        try:
            res = json.loads(m.group(0)) if m else {}
        except ValueError:
            res = {}
        for e in chunk:
            tried.add(e["id"])
            r = res.get(e["id"]) or {}
            tm = r.get("time")
            if isinstance(tm, str) and re.fullmatch(r"\d{1,2}:\d{2}", tm.strip()):
                e["time"] = tm.strip().zfill(5); n += 1
                tms = {d: t for d, t in (r.get("times") or {}).items()
                       if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)) and re.fullmatch(r"\d{1,2}:\d{2}", str(t))}
                if tms:
                    e["times"] = {d: t.zfill(5) for d, t in tms.items()}
    st = load_json(STATE_FILE, st)
    st["time_tried"] = sorted(tried)[-5000:]
    save_json(STATE_FILE, st)
    log(f"время: уточнено {n} из {len(todo)}")
    return n


FEST_PROMPT = """Сегодня {today}. Найди только в приложенном источнике ПРОГРАММУ события:
{item}
Верни ОТДЕЛЬНОЕ событие на каждый концерт / спектакль / показ / лекцию / выставку программы, которые проходят
не раньше {today}: свои дата, время начала, площадка. Сверь год и даты с периодом именно этой редакции фестиваля. Исключай йогу, медитацию, ретриты и другие занятия без прямой связи с искусством. Не выдумывай: включай только то, что нашёл.
Если программы нет — верни []. Верни ТОЛЬКО JSON-массив:
[{{"title":"","title_en":"","who":"","cat":"music|soundart|club|media|gallery|performance|fair|theatre|biennial|cinema|lecture",
"venue":"","address":"","start":"YYYY-MM-DD","time":"HH:MM|null","desc":"","desc_en":"","url":null}}]"""


def expand_festivals(master, limit=8):
    """Фестивали и многодневные программы (кроме выставок) — раскладываем на отдельные события."""
    st = load_json(STATE_FILE, {"seen": [], "pages": {}})
    tried = set(st.get("fest_tried", []))
    todo = [e for e in master if e["id"] not in tried and _multi(e) and e.get("cat") != "gallery"
            and not e.get("festival") and (pdate(e.get("end")) or TODAY) >= TODAY
            and ((pdate(e.get("end")) - pdate(e.get("start"))).days <= 45)]
    todo.sort(key=lambda e: (-e.get("importance", 3), e.get("start") or ""))
    added = 0
    for parent in todo[:limit]:
        item = json.dumps({k: parent.get(k) for k in ("title", "who", "city", "venue", "start", "end", "src")}, ensure_ascii=False)
        try:
            sources = source_material([parent])
            if not sources:
                continue
            text = llm_text(FEST_PROMPT.format(today=TODAY.isoformat(), item=item) + "\nИсточники:\n" + sources)
        except Exception as ex:
            log("  ! программа:", ex)
            break
        m = re.search(r"\[.*\]", text, re.S)
        try:
            subs = json.loads(m.group(0)) if m else []
        except ValueError:
            subs = []
        tried.add(parent["id"])
        kids = []
        first, last = event_dates(parent)
        for k in subs if isinstance(subs, list) else []:
            if not isinstance(k, dict) or not k.get("title"):
                continue
            day = pdate(k.get("start"))
            if not day or not first or not last or not first <= day <= last:
                continue
            ev = {"title": k["title"], "title_en": k.get("title_en") or "", "who": k.get("who") or "",
                  "cat": k.get("cat") if k.get("cat") in CATS else parent.get("cat"),
                  "venue": k.get("venue") or parent.get("venue"), "address": k.get("address") or "",
                  "start": k["start"], "end": None,
                  "time": k["time"] if isinstance(k.get("time"), str) and re.fullmatch(r"\d{1,2}:\d{2}", k["time"]) else None,
                  "desc": k.get("desc") or "", "desc_en": k.get("desc_en") or "", "festival": parent["title"],
                  "src": k.get("url") or parent.get("src"), "srcName": parent.get("srcName"),
                  "importance": parent.get("importance", 3)}
            for f in ("region", "country", "country_en", "city", "city_en", "tz"):
                ev[f] = parent.get(f)
            if ev["time"]:
                ev["time"] = ev["time"].zfill(5)
            kids.append(ev)
        n = merge(master, kids)
        added += n
        log(f"  программа «{parent['title'][:40]}»: {n} событий")
    st = load_json(STATE_FILE, st)
    st["fest_tried"] = sorted(tried)[-3000:]
    save_json(STATE_FILE, st)
    return added


def build():
    master = load_json(EVENTS_FILE, [])
    rules = editor_rules()
    for ev in rules["events"]:
        if ev.get("id") and not any(x["id"] == ev["id"] for x in master):
            ev.setdefault("region", "ru"); ev.setdefault("importance", 4)
            master.append(ev)
    for ev in master:
        normalize_stage_city(ev)
    for ev in master:                      # клубная электроника и саунд-арт — свои рубрики
        if ev.get("cat") == "music" and is_club(ev):
            ev["cat"] = "club"
        elif not ev.get("cat_locked") and is_soundart(ev):
            ev["cat"] = "soundart"
    gone = dedupe(master)
    if gone:
        log(f"build: убрано дубликатов {gone}")
    hidden = set(rules["hide"])
    for ev in master:
        if ev["id"] in rules["pin"] or set(ev.get("aliases", [])) & set(rules["pin"]):
            ev["importance"] = 5
    base_url = os.environ.get("SITE_URL", "")
    live = []
    for ev in master:
        if ev["id"] not in hidden and not outside_scope(ev) and current_event(ev):
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
            ves_one = [ve]
            s0, e0 = pdate(ev.get("start")), pdate(ev.get("end"))
            if p[3] and s0 and e0 and 0 < (e0 - s0).days <= 7:    # несколько показов — событие на каждый день
                tz = ZoneInfo(ev.get("tz") or "Europe/Moscow")
                for k in range(1, (e0 - s0).days + 1):
                    d = s0 + dt.timedelta(days=k)
                    tm = (ev.get("times") or {}).get(d.isoformat(), ev["time"])
                    try:
                        h, m = map(int, tm.split(":"))
                        t0 = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=tz).astimezone(dt.timezone.utc)
                        ves_one.append(vevent({**ev, "id": f"{ev['id']}-{k}"}, (p[0], t0, t0 + dt.timedelta(hours=2), True), stamp, base_url))
                    except Exception:
                        pass
            (SITE / "ics" / f"{ev['id']}.ics").write_text(calendar(ev["title"], ves_one, feed=False), encoding="utf-8", newline="")
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
    if cmd in ("times", "collect", "all"):
        m = load_json(EVENTS_FILE, [])
        changed = expand_festivals(m)
        changed += fill_times(m)
        if changed:
            save_json(EVENTS_FILE, m)
    if cmd in ("build", "all"):
        build()
