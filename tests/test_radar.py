import datetime as dt

import pytest

from scraper import robot


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(robot, "TODAY", dt.date(2026, 11, 26))


@pytest.mark.parametrize(
    ("start", "end", "tba", "expected"),
    [
        ("2025-11-28", None, False, False),
        ("2025-12", None, True, False),
        ("2026-10", None, True, False),
        ("2026-11", None, True, True),
        ("2026-02-30", None, False, False),
        ("2026-11-29", "2026-11-28", False, False),
        ("2026-11-01", "2027-01-10", False, True),
        ("2027-03-12", None, False, True),
    ],
)
def test_current_event(start, end, tba, expected):
    assert robot.current_event({"start": start, "end": end, "tba": tba}) is expected


@pytest.mark.parametrize(
    ("date_quote", "announcement", "published", "start", "expected"),
    [
        ("28 ноября 2025", "Архив: 28 ноября 2025", None, "2026-11-28", False),
        ("28 ноября 2027", "Афиша: 28 ноября 2027", None, "2027-11-28", True),
        ("28 ноября", "Афиша: 28 ноября", "2025-11-20", "2026-11-28", False),
        ("19 января", "Афиша: 19 января", "2026-12-01", "2027-01-19", True),
        ("28 ноября 2026", "Архив: 28 ноября 2025", None, "2026-11-28", False),
    ],
)
def test_source_confirms_year(date_quote, announcement, published, start, expected):
    event = {"start": start, "date_quote": date_quote}
    assert robot.source_confirms_date(event, {"text": announcement, "date": published}) is expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Музей йоги: аудиовизуальное путешествие", True),
        ("Медитативный вечер в Планетарии 1", True),
        ("Guided Meditation", True),
        ("Практика цигун", True),
        ("Выставка Ильи Жаркова «Ботанические медитации»", False),
        ("Саунд-арт и полевые записи", False),
    ],
)
def test_editorial_scope(title, expected):
    assert robot.outside_scope({"title": title}) is expected


@pytest.mark.parametrize(("venue", "src", "city"), [
    ("Новая сцена", "https://t.me/newstageprojects/3197", "Санкт-Петербург"),
    ("Новая сцена им. Вс. Мейерхольда", "https://t.me/newstageprojects/3196", "Санкт-Петербург"),
    ("Большой театр (Новая сцена)", "https://t.me/bolshoi_theatre/11905", "Москва"),
    ("Театр Et Cetera", "https://t.me/newstageprojects/1", "Москва"),
])
def test_stage_city(venue, src, city):
    event = {"city": "Москва", "venue": venue, "src": src}
    robot.normalize_stage_city(event)
    assert event["city"] == city


# Эталон по редакционным замечаниям и программе t.me/moscownoisemanufactory/1151.
# Дата проверки фиксирована до открытия фестиваля.
EDITORIAL_CASES = [
    ("index-fest-2026-vladimir-martynov-index-iii-psaruman-moscow", "soundart", "11-25", "19:00", "Москва"),
    ("indexfest-index-solo", "soundart", "11-25", "21:00", "Москва"),
    ("indexfest-rushana-stolyarov", "soundart", "11-26", "20:00", "Москва"),
    ("indexfest-nesterov-mirele", "soundart", "11-27", "19:00", "Москва"),
    ("indexfest-zerolines", "soundart", "11-27", "21:00", "Москва"),
    ("indexfest-vasiliev-arkadius-padre", "soundart", "11-28", "21:00", "Москва"),
    ("index-fest-2026-index-iii-resonance-party-moscow", "club", "11-28", "23:00", "Москва"),
    ("indexfest-friends-closing", "soundart", "11-29", "19:00", "Москва"),
    ("snm-magiya-prisutstviya", "music", "11-19", "19:00", "Москва"),
    ("snm-magiya-lecture", "lecture", "11-19", "17:00", "Москва"),
    ("course-psychoacoustics-phenomenology-of-sound-moscow", "soundart", "11-25", "19:00", "Москва"),
    ("ilya-zharkov-botanical-meditations-st-petersbur", "gallery", "11-13", None, "Санкт-Петербург"),
    ("program-of-works-by-alexander-scriabin-moscow", "music", "11-28", "19:30", "Санкт-Петербург"),
]
EXCLUDED_CASES = [
    "index-fest-2026-rushana-anton-stolyarov-index-iii-dmitry-ero-moscow",
    "index-fest-2026-index-iii-solo-concert-moscow",
    "index-fest-2026-oleg-nesterov-mire-le-anastasia-terelya-inde-moscow",
    "index-fest-2026-xandr-vasiliev-arkadius-padre-moscow",
    "index-fest-2026-zerolines-index-iii-dmitry-eroshin-dmitry-re-moscow",
    "resonance-party-at-rndm-club-moscow",
    "index-fest-iii-contemporary-music-festival-moscow",
    "index-fest-opening-concert-moscow",
    "botanical-meditations-saint-peters",
    "created-nature-concert-by-studio-of-new-music-ensemble-moscow",
    "yoga-museum-audiovisual-journey-through-centuries-st-petersbur",
    "meditative-evening-at-planetarium-1-nizhny-novgo",
]


def test_editorial_examples_through_build(tmp_path, monkeypatch):
    master = robot.load_json(robot.EVENTS_FILE, [])
    by_id = {e['id']: e for e in master}
    wanted = {row[0] for row in EDITORIAL_CASES} | set(EXCLUDED_CASES)
    fixtures = [by_id[key] for key in sorted(wanted)]
    monkeypatch.setattr(robot, 'TODAY', dt.date(2026, 11, 19))
    monkeypatch.setattr(robot, 'EVENTS_FILE', tmp_path / 'master.json')
    monkeypatch.setattr(robot, 'SITE', tmp_path / 'site')
    monkeypatch.setenv('AFISHA_IMAGES', '0')
    robot.save_json(robot.EVENTS_FILE, fixtures)
    robot.build()
    public = {e['id']: e for e in robot.load_json(robot.SITE / 'data/events.json', {})['events']}
    assert not set(EXCLUDED_CASES).intersection(public)
    for key, cat, day, clock, city in EDITORIAL_CASES:
        actual = public[key]
        assert (actual['cat'], actual['start'], actual.get('time'), actual['city']) == (cat, '2026-' + day, clock, city), key


def test_bot_date_search():
    from bot import bot
    sample = dict(id='show', title='Выставка', city='Москва', region='ru', src='https://example.org', start='2026-11-24', end='2026-11-27')
    rows = [sample, {**sample, 'city': 'Казань', 'title': 'Другой город'}, {**sample, 'tba': True, 'title': 'Без даты'}]
    result = bot.date_reply(rows, 'Москва', ['26.11.2026'])
    assert 'Выставка' in result and 'Другой город' not in result and 'Без даты' not in result
    assert 'событий нет' in bot.date_reply(rows, 'Москва', ['2026-11-28'])
    assert 'Проверьте дату' in bot.date_reply(rows, 'Москва', ['31.11.2026'])
