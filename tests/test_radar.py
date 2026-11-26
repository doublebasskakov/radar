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
