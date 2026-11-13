(function () {
  "use strict";
  const CFG = window.AFISHA_CONFIG || {};
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("afisha:" + k); return v == null ? d : JSON.parse(v); } catch (_) { return d; } },
    set(k, v) { try { localStorage.setItem("afisha:" + k, JSON.stringify(v)); } catch (_) {} },
  };

  // ------------------------------------------------------------ i18n
  const T = {
    ru: {
      brand: "Радар", brandSub: "современное искусство", tabRu: "Россия", tabWorld: "Мир", tabFav: "Избранное", tabSubs: "Подписки",
      heroRu: "Россия", heroRuSub: "Новая музыка, медиа-арт, выставки, кино, лекции, перформанс и театр — во всех городах. Обновляется каждый день.",
      heroWorld: "Мир", heroWorldSub: "Биеннале, фестивали медиаискусства и новой музыки, ярмарки и главные музейные выставки — на год вперёд.",
      heroFav: "Избранное", heroFavSub: "События, отмеченные звёздочкой. Хранятся на этом устройстве.",
      picks: "Выбор редакции", picksSub: "главное в ближайший месяц",
      allPlaces: "Все города", allCountries: "Все страны", pickCity: "Выберите город", pickCountry: "Выберите страну", placeSearch: "Найти город…", morePlaces: "Ещё…", all: "Всё",
      whenAll: "Всё время", whenToday: "Сегодня", whenWeekend: "Выходные", whenWeek: "7 дней", whenMonth: "Месяц",
      search: "Поиск: художник, площадка, композитор…",
      soon: "Ближайшие", live: "Уже идут", liveSub: "по дате закрытия", tba: "Дата уточняется", nothing: "Ничего не нашлось — попробуйте снять фильтры.",
      favEmpty: "Пока пусто. Нажмите ☆ на карточке, чтобы сохранить событие.",
      addCal: "+ В календарь", calWhich: "В какой календарь добавлять?", calApple: "Apple Календарь (iPhone, Mac)", calGoogle: "Google Календарь", calHint: "Запомню выбор. Сменить можно во вкладке «Подписки».", calNow: "Кнопка «В календарь» добавляет в:", calChange: "Сменить", findMore: "🔎 Найти больше", mineBadge: "моя находка", myTitle: "Личный поиск", myLead: "Робот ищет события в интернете по вашему городу — за счёт вашей бесплатной квоты Google Gemini. Находки видите только вы.", myKey: "Ключ Gemini API", myKeyHelp: "Получите бесплатный ключ на aistudio.google.com/apikey — войдите своим Google-аккаунтом (из России сервис открывается только с VPN, и поиск тоже работает только с VPN) — и вставьте сюда. Ключ хранится только на этом устройстве.", mySave: "Сохранить ключ", myTopic: "Что ищем (необязательно): например, «саунд-арт» или «выставки фотографии»", myRun: "Искать", myBusy: "Ищу… это займёт 20–60 секунд", myFound: "Найдено новых:", myNone: "Ничего нового не нашлось — попробуйте другой запрос.", myErr: "Ошибка поиска:", myForget: "Удалить ключ", myClear: "Очистить мои находки", myWhere: "Где ищем:", myYaHelp: "Для поиска через Яндекс нужен аккаунт Yandex Cloud с подключённым Search API и YandexGPT: создайте сервисный аккаунт с ролями search-api.webSearch.user и ai.languageModels.user, выпустите API-ключ и укажите ID каталога. Поиск оплачивается с вашего счёта Yandex Cloud (копейки за запрос). Ключ хранится только на этом устройстве.", press: "пресс-показ · по аккредитации", pressChip: "Пресс-показы", source: "Источник", share: "Поделиться", more: "Показать ещё",
      liveBadge: "идёт", newBadge: "новое", until: "до", fromTg: "из Telegram",
      favIcs: "Всё избранное в календарь", copied: "Ссылка скопирована", saved: "Добавлено в избранное", removed: "Убрано из избранного",
      updated: "Обновлено", events: "событий",
      subsTitle: "Подписки", subsLead: "Подпишитесь один раз — новые события сами появятся в вашем календаре (iPhone, Mac, Google, Outlook).",
      subApple: "Apple / iPhone", subGoogle: "Google", subCopy: "Скопировать ссылку",
      feedAll: "Вся афиша", feedPicks: "Только выбор редакции", feedCity: "Город", feedCat: "Жанр",
      botTitle: "Telegram-бот с дайджестом", botLead: "Каждый понедельник — главное на неделю в вашем городе и мире.",
      installTitle: "Установить на телефон", installIos: "iPhone: откройте в Safari → «Поделиться» → «На экран „Домой“».",
      installAndroid: "Android: меню Chrome → «Установить приложение».", installBtn: "Установить",
      footNote: "Афиша собирается автоматически из Telegram-каналов площадок, сайтов и подборок. Перед походом проверяйте дату по ссылке «Источник». Изображения принадлежат правообладателям и ведут на первоисточник.",
      suggest: "Предложить событие или источник", region: "Россия", world: "Мир", imgFrom: "Изображение:",
      cats: { music: "Новая музыка", media: "Медиа / диджитал", gallery: "Выставки", performance: "Перформанс", fair: "Ярмарки / фестивали", theatre: "Театр", cinema: "Кино", lecture: "Лекции", biennial: "Биеннале" },
      mon: ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"],
      mon1: ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"],
      wd: ["вс","пн","вт","ср","чт","пт","сб"],
    },
    en: {
      brand: "Radar", brandSub: "contemporary art", tabRu: "Russia", tabWorld: "World", tabFav: "Saved", tabSubs: "Subscribe",
      heroRu: "Russia", heroRuSub: "New music, media art, exhibitions, cinema, talks, performance and theatre across the country. Updated daily.",
      heroWorld: "World", heroWorldSub: "Biennials, media-art and new-music festivals, fairs and major museum shows — a year ahead.",
      heroFav: "Saved", heroFavSub: "Events you starred. Stored on this device.",
      picks: "Editors' picks", picksSub: "the essentials for the coming month",
      allPlaces: "All cities", allCountries: "All countries", pickCity: "Choose a city", pickCountry: "Choose a country", placeSearch: "Find a city…", morePlaces: "More…", all: "All",
      whenAll: "Any time", whenToday: "Today", whenWeekend: "Weekend", whenWeek: "7 days", whenMonth: "Month",
      search: "Search: artist, venue, composer…",
      soon: "Coming up", live: "On now", liveSub: "by closing date", tba: "Date TBA", nothing: "Nothing found — try clearing filters.",
      favEmpty: "Nothing yet. Tap ☆ on a card to save an event.",
      addCal: "+ Add to calendar", calWhich: "Which calendar do you use?", calApple: "Apple Calendar (iPhone, Mac)", calGoogle: "Google Calendar", calHint: "I'll remember your choice. Change it in the Subscriptions tab.", calNow: "“Add to calendar” goes to:", calChange: "Change", findMore: "🔎 Find more", mineBadge: "my find", myTitle: "Personal search", myLead: "The robot searches the web for events in your city using your own free Google Gemini quota. Only you see the results.", myKey: "Gemini API key", myKeyHelp: "Get a free key at aistudio.google.com/apikey (sign in with your Google account) and paste it here. The key stays on this device only.", mySave: "Save key", myTopic: "What to look for (optional): e.g. “sound art” or “photography shows”", myRun: "Search", myBusy: "Searching… 20–60 seconds", myFound: "New events found:", myNone: "Nothing new — try another query.", myErr: "Search error:", myForget: "Delete key", myClear: "Clear my finds", myWhere: "Searching in:", myYaHelp: "Yandex search needs a Yandex Cloud account with Search API and YandexGPT enabled: create a service account with roles search-api.webSearch.user and ai.languageModels.user, issue an API key and enter the folder ID. Billed to your Yandex Cloud account. The key stays on this device.", press: "press screening · accreditation", pressChip: "Press screenings", source: "Source", share: "Share", more: "Show more",
      liveBadge: "on now", newBadge: "new", until: "until", fromTg: "via Telegram",
      favIcs: "Add all saved to calendar", copied: "Link copied", saved: "Saved", removed: "Removed",
      updated: "Updated", events: "events",
      subsTitle: "Subscribe", subsLead: "Subscribe once and new events will appear in your calendar automatically (iPhone, Mac, Google, Outlook).",
      subApple: "Apple / iPhone", subGoogle: "Google", subCopy: "Copy link",
      feedAll: "Everything", feedPicks: "Editors' picks only", feedCity: "City", feedCat: "Genre",
      botTitle: "Telegram digest bot", botLead: "Every Monday — the week's highlights in your city and worldwide.",
      installTitle: "Install on your phone", installIos: "iPhone: open in Safari → Share → Add to Home Screen.",
      installAndroid: "Android: Chrome menu → Install app.", installBtn: "Install",
      footNote: "Listings are collected automatically from venues' Telegram channels, websites and editorial round-ups. Check the date via “Source” before you go. Images belong to their owners and link to the original.",
      suggest: "Suggest an event or a source", region: "Russia", world: "World", imgFrom: "Image:",
      cats: { music: "New music", media: "Media / digital", gallery: "Exhibitions", performance: "Performance", fair: "Fairs / festivals", theatre: "Theatre", cinema: "Cinema", lecture: "Talks", biennial: "Biennials" },
      mon: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
      mon1: ["January","February","March","April","May","June","July","August","September","October","November","December"],
      wd: ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],
    },
  };
  const CAT_HEX = { music: "#7cf2c9", media: "#8f7bff", gallery: "#ffb15c", performance: "#ff6b8b", fair: "#5cc8ff", theatre: "#ff4d3d", cinema: "#c9b6ff", lecture: "#f2e6c9", biennial: "#e7ff5c" };

  // ------------------------------------------------------------ state
  const S = {
    lang: store.get("lang", (navigator.language || "ru").startsWith("ru") ? "ru" : "en"),
    tab: "ru", place: { ru: store.get("place-ru", "all"), world: store.get("place-world", "all") },
    cat: "all", when: "all", q: "", shown: 48,
    fav: new Set(store.get("fav", [])), data: null,
  };
  const t = (k) => T[S.lang][k] ?? T.ru[k] ?? k;
  const L = (ev, f) => (S.lang === "en" && ev[f + "_en"]) ? ev[f + "_en"] : ev[f];

  // dates (по Москве)
  const nowMsk = new Date(Date.now() + 3 * 3600e3);
  const TODAY = Date.UTC(nowMsk.getUTCFullYear(), nowMsk.getUTCMonth(), nowMsk.getUTCDate());
  const D = (s) => (s && s.length === 10 ? Date.parse(s + "T00:00:00Z") : null);
  const DAY = 864e5;
  const fmtD = (ms, year) => { const d = new Date(ms); const y = d.getUTCFullYear(); const m = t("mon")[d.getUTCMonth()];
    const base = S.lang === "en" ? `${m} ${d.getUTCDate()}` : `${d.getUTCDate()} ${m}`;
    return base + (year && y !== new Date(TODAY).getUTCFullYear() ? " " + y : ""); };
  function whenText(e) {
    if (e.tba) { const [y, m] = String(e.start).split("-"); return `${t("mon1")[+m - 1]} ${y} · ${t("tba")}`; }
    const s = D(e.start), en = D(e.end);
    if (s && (!en || en === s)) return `${t("wd")[new Date(s).getUTCDay()]}, ${fmtD(s, true)}${e.time ? " · " + e.time : ""}`;
    if (s && en) return `${fmtD(s, new Date(s).getUTCFullYear() !== new Date(en).getUTCFullYear())} — ${fmtD(en, true)}`;
    if (en) return `${t("until")} ${fmtD(en, true)}`;
    return "";
  }
  const isLive = (e) => { const s = D(e.start), en = D(e.end); return !e.tba && en && en >= TODAY && (!s || s <= TODAY) && (!s || en > s); };
  const startKey = (e) => { if (e.tba) return 9e15; const s = D(e.start); return s && s >= TODAY ? s : (D(e.end) || TODAY); };
  function badge(e) {
    if (e.tba) return "TBA";
    const s = D(e.start), en = D(e.end), mon = (ms) => { const d = new Date(ms); return S.lang === "en" ? `${t("mon")[d.getUTCMonth()]} ${d.getUTCDate()}` : `${d.getUTCDate()} ${t("mon")[d.getUTCMonth()].slice(0, 3)}`; };
    if (s && s >= TODAY) return mon(s);
    return en ? `${t("until")} ${mon(en)}` : "";
  }
  function inWhen(e) {
    if (S.when === "all") return true;
    if (e.tba) return false;
    let from = TODAY, to;
    const wd = new Date(TODAY).getUTCDay();
    if (S.when === "today") to = TODAY;
    if (S.when === "week") to = TODAY + 7 * DAY;
    if (S.when === "month") to = TODAY + 31 * DAY;
    if (S.when === "weekend") {
      if (wd === 0) { from = TODAY; to = TODAY; }
      else { from = TODAY + (6 - wd) * DAY; to = from + DAY; }
    }
    const s = D(e.start) ?? -Infinity, en = D(e.end) ?? s;
    return s <= to && en >= from;
  }

  // ------------------------------------------------------------ covers
  function rng(seed) { let h = 2166136261; for (const c of seed) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return () => { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return ((h >>> 0) % 10000) / 10000; }; }
  function genCover(e) {
    const r = rng(e.id), c = CAT_HEX[e.cat] || "#fff", W = 480, H = 300; let g = "";
    const f = (n) => n.toFixed(0);
    if (e.cat === "music") {
      for (let k = 0, n = 5 + ~~(r() * 4); k < n; k++) { let d = `M0 ${H / 2}`; const a = 20 + r() * 90, fr = .008 + r() * .03, ph = r() * 6, y0 = H * (.2 + .6 * r());
        for (let x = 0; x <= W; x += 8) d += ` L${x} ${(y0 + Math.sin(x * fr + ph) * a * Math.sin(x / W * Math.PI)).toFixed(1)}`;
        g += `<path d="${d}" fill="none" stroke="${c}" stroke-opacity="${(.25 + .6 * r()).toFixed(2)}" stroke-width="${(1 + r() * 2.5).toFixed(1)}"/>`; }
      for (let x = 0; x < W; x += 12) { const h = 4 + r() * 60; g += `<rect x="${x}" y="${f(H - h)}" width="6" height="${f(h)}" fill="${c}" opacity=".18"/>`; }
    } else if (e.cat === "media") {
      const s = 20 + ~~(r() * 20);
      for (let y = 0; y < H; y += s) for (let x = 0; x < W; x += s) { const v = r(); if (v > .55) g += `<rect x="${x}" y="${y}" width="${s - 3}" height="${s - 3}" fill="${v > .9 ? "#fff" : c}" opacity="${(v > .9 ? .85 : v - .5).toFixed(2)}"/>`; }
      for (let k = 0; k < 6; k++) g += `<rect x="${f((r() - .5) * 80)}" y="${f(r() * H)}" width="${W}" height="${f(2 + r() * 10)}" fill="${c}" opacity=".35"/>`;
    } else if (e.cat === "performance") {
      const cx = W * (.3 + .4 * r()), cy = H * (.3 + .4 * r());
      for (let k = 14; k > 0; k--) g += `<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(k * 18 + r() * 8)}" fill="none" stroke="${c}" stroke-opacity="${(.08 + k * .03).toFixed(2)}" stroke-width="${(1 + r() * 3).toFixed(1)}"/>`;
    } else if (e.cat === "theatre") {
      const cx = W * (.25 + .5 * r());
      g += `<defs><radialGradient id="sp${e.id}" cx="${(cx / W).toFixed(2)}" cy=".75" r=".45"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs><polygon points="${f(cx - 14)},0 ${f(cx + 14)},0 ${f(cx + 120)},${H} ${f(cx - 120)},${H}" fill="url(#sp${e.id})"/>`;
      for (const side of [0, 1]) { const n = 7, w = W * (.18 + .1 * r()); for (let k = 0; k < n; k++) { const x0 = side ? W - w + k * w / n : k * w / n, b = (side ? -1 : 1) * (10 + r() * 20);
        g += `<path d="M${f(x0)} 0 Q ${f(x0 + b)} ${H / 2} ${f(x0)} ${H} L ${f(x0 + w / n)} ${H} Q ${f(x0 + w / n + b)} ${H / 2} ${f(x0 + w / n)} 0 Z" fill="${c}" opacity="${(.35 + .5 * (k % 2)).toFixed(2)}"/>`; } }
      g += `<rect width="${W}" height="26" fill="${c}" opacity=".9"/>`;
    } else if (e.cat === "fair") {
      for (let k = 0; k < 26; k++) { const w = 30 + r() * 140, h = 30 + r() * 110; g += `<rect x="${f(r() * W - w / 2)}" y="${f(r() * H - h / 2)}" width="${f(w)}" height="${f(h)}" fill="none" stroke="${r() > .8 ? "#fff" : c}" stroke-opacity="${(.2 + r() * .6).toFixed(2)}" stroke-width="2"/>`; }
    } else if (e.cat === "cinema") {
      const y0 = H * (.18 + .2 * r()), h = H * .5;
      g += `<rect x="0" y="${f(y0)}" width="${W}" height="${f(h)}" fill="${c}" opacity=".16"/>`;
      for (let x = 6; x < W; x += 22) { g += `<rect x="${x}" y="${f(y0 + 6)}" width="10" height="8" rx="2" fill="${c}" opacity=".7"/><rect x="${x}" y="${f(y0 + h - 14)}" width="10" height="8" rx="2" fill="${c}" opacity=".7"/>`; }
      for (let x = 10, k = 0; x < W; x += 116, k++) { const o = (.25 + r() * .6).toFixed(2); g += `<rect x="${x}" y="${f(y0 + 22)}" width="100" height="${f(h - 44)}" fill="${k % 2 ? "#fff" : c}" opacity="${o}"/>`; }
      g += `<circle cx="${f(W * (.2 + .6 * r()))}" cy="${f(H * .85)}" r="${f(40 + r() * 60)}" fill="${c}" opacity=".12"/>`;
    } else if (e.cat === "lecture") {
      for (let y = 40; y < H; y += 22) { const w = 120 + r() * 300; g += `<rect x="40" y="${y}" width="${f(w)}" height="7" rx="3" fill="${c}" opacity="${(.15 + r() * .5).toFixed(2)}"/>`; }
      g += `<circle cx="${f(W * .78)}" cy="${f(H * .42)}" r="${f(50 + r() * 30)}" fill="none" stroke="${c}" stroke-width="3" opacity=".8"/><path d="M${f(W * .78 - 30)} ${f(H * .62)} q30 30 60 0" stroke="${c}" stroke-width="3" fill="none" opacity=".8"/>`;
    } else if (e.cat === "biennial") {
      for (let k = 0; k < 9; k++) { const R = 30 + k * 26; g += `<circle cx="${W / 2}" cy="${H / 2}" r="${R}" fill="none" stroke="${c}" stroke-opacity="${(.15 + r() * .6).toFixed(2)}" stroke-width="${(1 + r() * 6).toFixed(1)}" stroke-dasharray="${f(4 + r() * 40)} ${f(4 + r() * 30)}"/>`; }
    } else {
      for (let k = 0; k < 7; k++) { const x = r() * W, y = r() * H, s = 40 + r() * 160, tt = r();
        if (tt < .4) g += `<circle cx="${f(x)}" cy="${f(y)}" r="${f(s / 2)}" fill="${c}" opacity="${(.2 + r() * .6).toFixed(2)}"/>`;
        else if (tt < .75) g += `<rect x="${f(x)}" y="${f(y)}" width="${f(s)}" height="${f(s * .7)}" fill="${r() > .6 ? "#f4efe6" : c}" opacity="${(.25 + r() * .6).toFixed(2)}" transform="rotate(${f((r() - .5) * 40)} ${f(x)} ${f(y)})"/>`;
        else g += `<polygon points="${f(x)},${f(y - s / 2)} ${f(x + s / 2)},${f(y + s / 2)} ${f(x - s / 2)},${f(y + s / 2)}" fill="none" stroke="${c}" stroke-width="3" opacity=".8"/>`; }
    }
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="${W}" height="${H}" fill="#0d0d12"/>${g}</svg>`;
  }
  const cover = (e) => e.img ? `<img src="${esc(e.img)}" alt="" loading="lazy" decoding="async" onerror="this.outerHTML=window.__gen('${esc(e.id)}')">` : genCover(e);
  window.__gen = (id) => genCover(S.data.events.find((x) => x.id === id) || { id, cat: "gallery" });

  // ------------------------------------------------------------ card
  function place(e) { return e.region === "world" ? `${L(e, "city")}, ${L(e, "country")}` : L(e, "city"); }
  const UA = navigator.userAgent;
  const APPLE = /iPhone|iPad|iPod|Macintosh/.test(UA) && !/Android/.test(UA);
  function calButtons(e) {
    if (!e.ics) return `<span class="btn" aria-disabled="true">${t("tba")}</span>`;
    // Одна кнопка: на iPhone/Mac — файл .ics (сразу открывается Календарь), на остальных — Google Календарь
    return `<button class="btn primary" type="button" title="${esc(e.calSummary || "")}" data-cal>${t("addCal")}</button>`;
  }
  // Добавление в календарь: первый раз спрашиваем, какой календарь, дальше — в одно касание.
  function openExternal(url) {
    const TGW = window.Telegram && window.Telegram.WebApp;
    if (IN_TG && TGW && TGW.openLink && /^https?:/.test(url)) { TGW.openLink(url); return; }   // из Telegram — во внешний браузер
    const w = window.open(url, "_blank");
    if (w) { try { w.opener = null; } catch (_) {} } else location.href = url;   // всплывающее окно заблокировано — открываем здесь
  }
  function addToCal(e, kind) {
    if (kind === "google" || !e.ics) return openExternal(e.gcal);
    if (/^data:/.test(e.ics)) {            // личная находка: файл собран в браузере
      if (IN_TG) return openExternal(e.gcal);
      const a = document.createElement("a"); a.href = e.ics; a.download = "event.ics"; document.body.appendChild(a); a.click(); a.remove(); return;
    }
    if (IN_TG) {
      // Из Telegram ссылка на .ics уходит прямо в Календарь как «подписка». Поэтому открываем
      // в Safari промежуточную страницу — там файл открывается как одно событие «Добавить в Календарь».
      const TGW = window.Telegram && window.Telegram.WebApp;
      const page = new URL("add.html?k=apple&id=" + encodeURIComponent(e.id), location.href).href;
      if (TGW && TGW.openLink) return TGW.openLink(page, { try_instant_view: false });
      return openExternal(page);
    }
    location.href = new URL(e.ics, location.href).href;
  }
  function calChoice(e, force) {
    const saved = store.get("cal", "");
    if (saved && !force) return addToCal(e, saved);
    let box = $("#calSheet");
    if (!box) { box = document.createElement("div"); box.id = "calSheet"; box.className = "sheet"; document.body.appendChild(box); }
    box.innerHTML = `<div class="sheet-in"><h3>${esc(t("calWhich"))}</h3>
      <button class="pitem" data-k="apple"><span> ${esc(t("calApple"))}</span></button>
      <button class="pitem" data-k="google"><span>${esc(t("calGoogle"))}</span></button>
      <p class="hint">${esc(t("calHint"))}</p></div>`;
    box.hidden = false;
    box.onclick = (ev) => {
      const b = ev.target.closest("[data-k]");
      box.hidden = true;
      if (!b) return;
      store.set("cal", b.dataset.k); render();
      if (e) addToCal(e, b.dataset.k);
    };
  }
  function card(e) {
    const c = t("cats")[e.cat] || e.cat, fav = S.fav.has(e.id);
    return `<article class="card" data-id="${esc(e.id)}">
      <div class="cover" data-open>${cover(e)}<span class="badge b-city">${esc(place(e))}</span>${isLive(e) ? `<span class="badge b-live">${t("liveBadge")}</span>` : ""}${e.mine ? `<span class="badge b-new">${t("mineBadge")}</span>` : e.isNew ? `<span class="badge b-new">${t("newBadge")}</span>` : ""}<span class="badge b-date">${esc(badge(e))}</span></div>
      <div class="body">
        <span class="tag" style="color:${CAT_HEX[e.cat] || "#fff"}">${esc(c)}${e.tg ? ` <span class="muted">· ${t("fromTg")}</span>` : ""}${e.press ? ` <span class="press">${t("press")}</span>` : ""}</span>
        <h3 class="title" data-open>${esc(L(e, "title"))}</h3>
        ${e.who ? `<div class="who">${esc(e.who)}</div>` : ""}
        <div class="when">${esc(whenText(e))}</div>
        <div class="venue">${esc(e.venue || "")}${e.address ? " · " + esc(e.address) : ""}</div>
        <p class="desc">${esc(L(e, "desc"))}</p>
        <div class="actions">${calButtons(e)}<button class="btn icon star${fav ? " on" : ""}" data-fav aria-label="★">${fav ? "★" : "☆"}</button><button class="btn icon" data-share aria-label="${t("share")}">↗</button></div>
      </div></article>`;
  }
  function detail(e) {
    const fav = S.fav.has(e.id);
    return `<div class="cover">${cover(e)}<span class="badge b-city">${esc(place(e))}</span></div>
      <div class="body">
        <span class="tag" style="color:${CAT_HEX[e.cat]}">${esc(t("cats")[e.cat] || e.cat)}</span>
        <h3 class="title">${esc(L(e, "title"))}</h3>
        ${e.who ? `<div class="who">${esc(e.who)}</div>` : ""}
        <div class="when">${esc(whenText(e))}</div>
        <div class="venue">${esc(e.venue || "")}${e.address ? " · " + esc(e.address) : ""}</div>
        <p class="desc">${esc(L(e, "desc"))}</p>
        <div class="actions">${calButtons(e)}<button class="btn star${fav ? " on" : ""}" data-fav>${fav ? "★" : "☆"} ${t("tabFav")}</button><button class="btn" data-share>${t("share")}</button><a class="btn" href="${esc(e.src)}" target="_blank" rel="noopener">${t("source")}: ${esc(e.srcName || "")} ↗</a></div>
        ${e.img && e.imgCredit ? `<div class="credit">${t("imgFrom")} ${esc(e.imgCredit)}</div>` : ""}
      </div>`;
  }

  // ------------------------------------------------------------ render
  function chips(el, items, cur, onPick) {
    el.innerHTML = items.map(([v, label, col]) => `<button class="chip${cur === v ? " on" : ""}" data-v="${esc(v)}">${col ? `<span class="dot" style="background:${col}"></span>` : ""}${esc(label)}</button>`).join("");
    el.onclick = (ev) => { const b = ev.target.closest(".chip"); if (b) onPick(b.dataset.v); };
  }
  function regionEvents() { return S.data.events.filter((e) => (e.region || "ru") === S.tab); }

  function renderFilters(evs) {
    const key = S.tab === "world" ? "country" : "city";
    const counts = {};
    evs.forEach((e) => { const k = e[key]; if (k) counts[k] = (counts[k] || 0) + 1; });
    let places = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    if (S.tab === "ru") places.sort((a, b) => (a[0] === "Москва" ? -1 : b[0] === "Москва" ? 1 : a[0] === "Онлайн" ? 1 : b[0] === "Онлайн" ? -1 : b[1] - a[1]));
    const labelOf = (name) => { if (S.lang !== "en") return name; const e = evs.find((x) => x[key] === name); return (e && e[key + "_en"]) || name; };
    const cur = S.place[S.tab];
    const top = places.slice(0, 5);
    const el = $("#fPlace");
    const curLabel = cur === "all" ? (S.tab === "world" ? t("allCountries") : t("allPlaces")) : labelOf(cur);
    el.innerHTML = `<button class="chip pick-place${cur !== "all" ? " on" : ""}" id="placeBtn">📍 ${esc(curLabel)} ▾</button>` +
      (cur !== "all" ? `<button class="chip" data-v="all">✕</button>` : "") +
      top.filter(([n]) => n !== cur).map(([n, c]) => `<button class="chip" data-v="${esc(n)}">${esc(labelOf(n))} · ${c}</button>`).join("");
    el.onclick = (ev) => {
      if (ev.target.closest("#placeBtn")) return openPlacePicker(places, labelOf);
      const b = ev.target.closest("button.chip[data-v]"); if (b) setPlace(b.dataset.v);
    };
    const cats = Object.keys(t("cats")).filter((k) => evs.some((e) => e.cat === k));
    const catItems = [["all", t("all")]].concat(cats.map((k) => [k, t("cats")[k], CAT_HEX[k]]));
    if (evs.some((e) => e.press)) catItems.push(["press", t("pressChip"), "#c9b6ff"]);
    chips($("#fCat"), catItems, S.cat, (v) => { S.cat = v; S.shown = 48; render(); });
    if (!$("#findMore")) { const b = document.createElement("button"); b.id = "findMore"; b.className = "chip pick-place"; $("#q").after(b); b.onclick = openMySearch; }
    $("#findMore").textContent = t("findMore");
    chips($("#fWhen"), [["all", t("whenAll")], ["today", t("whenToday")], ["weekend", t("whenWeekend")], ["week", t("whenWeek")], ["month", t("whenMonth")]], S.when, (v) => { S.when = v; S.shown = 48; render(); });
  }

  function openPlacePicker(places, labelOf) {
    const total = places.reduce((a, [, c]) => a + c, 0);
    const title = S.tab === "world" ? t("pickCountry") : t("pickCity");
    $("#modalBody").innerHTML = `<div class="body picker"><h3 class="title">${esc(title)}</h3>
      <input type="search" id="placeQ" placeholder="${esc(t("placeSearch"))}" autocomplete="off">
      <div class="plist" id="plist">${[["all", S.tab === "world" ? t("allCountries") : t("allPlaces"), total]].concat(places.map(([n, c]) => [n, labelOf(n), c]))
        .map(([v, l, c]) => `<button class="pitem${S.place[S.tab] === v ? " on" : ""}" data-place="${esc(v)}" data-label="${esc(String(l).toLowerCase())}"><span>${esc(l)}</span><b>${c}</b></button>`).join("")}</div></div>`;
    $("#modal").hidden = false; $("#modal").dataset.id = "";
    const q = $("#placeQ");
    q.oninput = () => { const v = q.value.trim().toLowerCase(); document.querySelectorAll("#plist .pitem").forEach((b) => { b.hidden = v && !b.dataset.label.includes(v); }); };
    $("#plist").onclick = (ev) => { const b = ev.target.closest("[data-place]"); if (!b) return; $("#modal").hidden = true; setPlace(b.dataset.place); };
    setTimeout(() => q.focus(), 50);
  }
  function setPlace(v) { S.place[S.tab] = v; store.set("place-" + S.tab, v); S.shown = 48; render(); }

  function render() {
    document.documentElement.lang = S.lang;
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = t(n.dataset.i18n); });
    $("#lang").textContent = S.lang === "ru" ? "EN" : "RU";
    $("#q").placeholder = t("search");
    document.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("on", b.dataset.tab === S.tab));
    $("#favCount").textContent = S.fav.size ? S.fav.size : "";
    $("#view-subs").hidden = S.tab !== "subs";
    $("#view-list").hidden = S.tab === "subs";
    if (!S.data) return;
    const u = S.data.updated ? D(S.data.updated) : null;
    $("#updated").textContent = `${u ? t("updated") + " " + fmtD(u, true) + " · " : ""}${S.data.count} ${t("events")}`;
    if (S.tab === "subs") return renderSubs();

    const isFav = S.tab === "fav";
    $("#heroTitle").textContent = t(isFav ? "heroFav" : S.tab === "world" ? "heroWorld" : "heroRu");
    $("#heroSub").textContent = t(isFav ? "heroFavSub" : S.tab === "world" ? "heroWorldSub" : "heroRuSub");
    $("#filters").hidden = isFav;

    let evs;
    if (isFav) {
      evs = S.data.events.filter((e) => S.fav.has(e.id));
      $("#picksWrap").hidden = true;
      const out = $("#list");
      if (!evs.length) { out.innerHTML = `<div class="empty">${t("favEmpty")}</div>`; return; }
      evs.sort((a, b) => startKey(a) - startKey(b));
      out.innerHTML = `<div class="actions" style="margin:6px 0 16px"><button class="btn primary" id="favIcs">${t("favIcs")}</button></div><div class="grid">${evs.map(card).join("")}</div>`;
      $("#favIcs").onclick = downloadFavIcs;
      return;
    }
    const base = regionEvents();
    renderFilters(base);
    const cur = S.place[S.tab], key = S.tab === "world" ? "country" : "city";
    const q = S.q.trim().toLowerCase();
    const list = base.filter((e) => (cur === "all" || e[key] === cur) && (S.cat === "all" || e.cat === S.cat || (S.cat === "press" && e.press)) && inWhen(e) &&
      (!q || [e.title, e.title_en, e.who, e.venue, e.desc, e.city, e.city_en, e.country].join(" ").toLowerCase().includes(q)));

    // picks
    const picks = base.filter((e) => (e.importance || 3) >= 4 && (cur === "all" || e[key] === cur) && !e.tba &&
      (D(e.start) ?? TODAY) <= TODAY + 45 * DAY && (D(e.end) ?? D(e.start)) >= TODAY).sort((a, b) => startKey(a) - startKey(b)).slice(0, 12);
    $("#picksWrap").hidden = !picks.length || !!q || S.cat !== "all" || S.when !== "all";
    $("#picks").innerHTML = picks.map(card).join("");

    const soon = list.filter((e) => !isLive(e)).sort((a, b) => startKey(a) - startKey(b));
    const live = list.filter(isLive).sort((a, b) => startKey(a) - startKey(b));
    const out = $("#list");
    if (!list.length) { out.innerHTML = `<div class="empty">${t("nothing")}</div>`; return; }
    const shownSoon = soon.slice(0, S.shown), shownLive = live.slice(0, Math.max(0, S.shown - shownSoon.length) || (soon.length >= S.shown ? 0 : live.length));
    out.innerHTML =
      (shownSoon.length ? `<h2>${t("soon")} <small class="muted">${soon.length}</small></h2><div class="grid">${shownSoon.map(card).join("")}</div>` : "") +
      (shownLive.length ? `<h2>${t("live")} <small class="muted">${live.length} · ${t("liveSub")}</small></h2><div class="grid">${shownLive.map(card).join("")}</div>` : "") +
      (soon.length + live.length > shownSoon.length + shownLive.length ? `<button class="btn more" id="more">${t("more")}</button>` : "");
    const m = $("#more"); if (m) m.onclick = () => { S.shown += 48; render(); };
  }


  // ------------------------------------------------------------ личный поиск (ключ пользователя)
  function myCreds() { return store.get("myCreds", null) || (store.get("gemini", "") ? { prov: "gemini", key: store.get("gemini", "") } : null); }
  function openMySearch(prov) {
    const cr = myCreds();
    const cur = S.place[S.tab];
    const where = cur === "all" ? (S.tab === "world" ? t("allCountries") : t("allPlaces")) : cur;
    const yandexOn = !!CFG.proxy;
    prov = prov || "gemini";
    let form;
    if (cr) {
      form = `<p><b>${t("myWhere")}</b> ${esc(where)}${S.tab === "world" ? "" : ", Россия"} · <span class="muted">${cr.prov === "yandex" ? "Яндекс" : "Gemini"}</span></p>
        <input type="search" id="myTopic" placeholder="${esc(t("myTopic"))}">
        <div class="actions"><button class="btn primary" id="myRun">${t("myRun")}</button><button class="btn" id="myForget">${t("myForget")}</button><button class="btn" id="myClear">${t("myClear")}</button></div>
        <div id="myOut" class="muted" style="margin-top:10px"></div>`;
    } else {
      const tabs = yandexOn ? `<div class="chips" style="margin:6px 0 10px"><button class="chip${prov === "gemini" ? " on" : ""}" data-prov="gemini">Google Gemini</button><button class="chip${prov === "yandex" ? " on" : ""}" data-prov="yandex">Яндекс (без VPN)</button></div>` : "";
      form = tabs + (prov === "yandex"
        ? `<label class="muted">${t("myYaHelp")}</label><input type="password" id="myKey" placeholder="API-ключ Yandex Cloud" autocomplete="off"><input type="text" id="myFolder" placeholder="ID каталога (folder ID)" autocomplete="off">
           <div class="actions"><a class="btn" href="https://yandex.cloud/ru/docs/search-api/quickstart/" target="_blank" rel="noopener">Инструкция ↗</a><button class="btn primary" id="mySave">${t("mySave")}</button></div>`
        : `<label class="muted">${t("myKeyHelp")}</label><input type="password" id="myKey" placeholder="${esc(t("myKey"))}" autocomplete="off">
           <div class="actions"><a class="btn" href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">aistudio.google.com ↗</a><button class="btn primary" id="mySave">${t("mySave")}</button></div>`);
    }
    $("#modalBody").innerHTML = `<div class="body picker"><h3 class="title">${t("myTitle")}</h3><p class="muted">${t("myLead")}</p>${form}</div>`;
    $("#modal").hidden = false; $("#modal").dataset.id = "";
    if (!cr) {
      document.querySelectorAll("[data-prov]").forEach((b) => (b.onclick = () => openMySearch(b.dataset.prov)));
      $("#mySave").onclick = () => {
        const key = $("#myKey").value.trim(); if (!key) return;
        if (prov === "yandex") { const folder = $("#myFolder").value.trim(); if (!folder) return; store.set("myCreds", { prov, key, folder }); }
        else store.set("myCreds", { prov: "gemini", key });
        openMySearch();
      };
      return;
    }
    $("#myForget").onclick = () => { store.set("myCreds", null); store.set("gemini", ""); openMySearch(); };
    $("#myClear").onclick = () => { store.set("mine", []); S.data.events = S.data.events.filter((e) => !e.mine); render(); toast("OK"); };
    $("#myRun").onclick = () => runMySearch(cr, cur, $("#myTopic").value.trim());
  }
  async function geminiModel(key) {
    const cached = store.get("geminiModel", ""); if (cached) return cached;
    try {
      const r = await fetch("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200&key=" + encodeURIComponent(key)).then((x) => x.json());
      const names = (r.models || []).filter((m) => (m.supportedGenerationMethods || []).includes("generateContent") && /flash/.test(m.name) && !/(tts|live|image|audio|lite)/.test(m.name)).map((m) => m.name.split("/").pop());
      names.sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
      const m = names[0] || "gemini-flash-latest"; store.set("geminiModel", m); return m;
    } catch (_) { return "gemini-flash-latest"; }
  }
  async function runMySearch(cr, place, topic) {
    const out = $("#myOut"); out.textContent = t("myBusy"); $("#myRun").disabled = true;
    const today = new Date(TODAY).toISOString().slice(0, 10);
    const region = S.tab === "world" ? (place === "all" ? "в мире (вне России)" : `в стране/городе: ${place}`) : (place === "all" ? "в городах России" : `в городе ${place} (Россия)`);
    const known = S.data.events.filter((e) => place === "all" || e.city === place || e.country === place).map((e) => e.title).slice(0, 150).join("; ");
    const prompt = `Сегодня ${today}. Найди в интернете (сайты площадок, афиши, Telegram-каналы) будущие события современного искусства ${region} на ближайшие 2 месяца${topic ? `, тема: ${topic}` : ""}: новая и экспериментальная музыка, саунд-арт, медиа- и цифровое искусство, выставки современного искусства, перформанс, современный театр и танец, артхаус-кино и кинофестивали, ярмарки, биеннале. Не включай уже известные: ${known}.
Верни ТОЛЬКО JSON-массив до 15 элементов: [{"title":"","who":"","cat":"music|media|gallery|performance|fair|theatre|cinema|biennial","city":"город по-русски","country":"страна по-русски","venue":"","address":"","start":"YYYY-MM-DD","end":"YYYY-MM-DD или null","time":"HH:MM или null","desc":"1–2 предложения своими словами","src":"URL источника"}]. Только события с подтверждённой датой и местом.`;
    try {
      let text;
      if (cr.prov === "yandex") {
        const where = place === "all" ? (S.tab === "world" ? "" : "Россия") : place;
        const theme = topic || "современное искусство";
        const queries = [`${theme} ${where} выставка афиша`, `концерт новой музыки ${where}`, `${where} медиаискусство перформанс афиша`, `артхаус кинопоказ ${where}`];
        const r = await fetch(CFG.proxy.replace(/\/$/, "") + "/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ apiKey: cr.key, folderId: cr.folder, queries, prompt }) });
        const j = await r.json(); if (!r.ok || j.error) throw new Error(j.error || r.status);
        text = j.text;
      } else {
        const key = cr.key;
        const model = await geminiModel(key);
        const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ role: "user", parts: [{ text: prompt }] }], tools: [{ google_search: {} }] }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error((j.error && j.error.message) || r.status);
        text = (j.candidates?.[0]?.content?.parts || []).map((p) => p.text || "").join("");
      }
      const arr = JSON.parse((text.match(/\[[\s\S]*\]/) || ["[]"])[0]);
      const have = new Set(S.data.events.map((e) => (e.title || "").toLowerCase().replace(/[^a-zа-я0-9]/g, "")));
      const fresh = arr.filter((e) => e && e.title && e.start && /^\d{4}-\d{2}-\d{2}$/.test(e.start) && (D(e.end) || D(e.start)) >= TODAY && !have.has(e.title.toLowerCase().replace(/[^a-zа-я0-9]/g, "")))
        .map((e, i) => ({ ...e, id: "mine-" + Date.now() + "-" + i, mine: true, region: S.tab === "world" ? "world" : "ru", cat: t("cats")[e.cat] ? e.cat : "gallery", srcName: (() => { try { return new URL(e.src).hostname.replace("www.", ""); } catch (_) { return ""; } })(),
          gcal: "https://calendar.google.com/calendar/render?" + new URLSearchParams({ action: "TEMPLATE", text: e.title, dates: e.start.replace(/-/g, "") + "/" + (e.end || e.start).replace(/-/g, ""), details: (e.desc || "") + "\n" + (e.src || ""), location: [e.venue, e.city].filter(Boolean).join(", ") }).toString() }))
        .map((e) => ({ ...e, ics: icsData(e) }));
      store.set("mine", store.get("mine", []).concat(fresh));
      S.data.events = S.data.events.concat(fresh);
      out.textContent = fresh.length ? `${t("myFound")} ${fresh.length}` : t("myNone");
      render();
    } catch (err) { out.textContent = `${t("myErr")} ${err.message || err}`; }
    $("#myRun").disabled = false;
  }
  function icsData(e) {
    const d = (x) => x.replace(/-/g, "");
    const endD = new Date(Date.parse((e.end || e.start) + "T00:00:00Z") + DAY).toISOString().slice(0, 10);
    const escI = (x) => String(x || "").replace(/[\\;,]/g, (m) => "\\" + m).replace(/\n/g, "\\n");
    const body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Radar//RU", "BEGIN:VEVENT", "UID:" + e.id + "@radar", "DTSTAMP:" + new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z",
      ...(/^\d{1,2}:\d{2}$/.test(e.time || "") ? ["DTSTART:" + d(e.start) + "T" + e.time.replace(":", "").padStart(4, "0") + "00", "DTEND:" + d(e.start) + "T" + String((+e.time.split(":")[0] + 2) % 24).padStart(2, "0") + e.time.split(":")[1] + "00"]
        : ["DTSTART;VALUE=DATE:" + d(e.start), "DTEND;VALUE=DATE:" + d(endD)]), "SUMMARY:" + escI(e.title), "LOCATION:" + escI([e.venue, e.city].filter(Boolean).join(", ")), "DESCRIPTION:" + escI((e.desc || "") + "\n" + (e.src || "")), "END:VEVENT", "END:VCALENDAR"].join("\r\n");
    return "data:text/calendar;charset=utf-8," + encodeURIComponent(body);
  }

  // ------------------------------------------------------------ subscriptions
  function feedUrl(path) { return new URL(path, location.href).href; }
  function renderSubs() {
    const feeds = S.data.feeds || [];
    const evs = S.data.events;
    const nameFor = (f) => {
      const [reg, kind, ...rest] = f.split("-"); const v = rest.join("-");
      const R = reg === "world" ? t("world") : t("region");
      if (kind === "all") return [R, t("feedAll")];
      if (kind === "picks") return [R, t("feedPicks")];
      if (kind === "cat") return [R, `${t("feedCat")}: ${t("cats")[v] || v}`];
      if (kind === "country") { const e = evs.find((x) => slugify(x.country_en || x.country) === v); return [R, e ? L(e, "country") : v]; }
      if (kind === "city") { const e = evs.find((x) => slugify(x.city_en || x.city) === v); return [R, `${t("feedCity")}: ${e ? L(e, "city") : v}`]; }
      return [R, f];
    };
    const order = (f) => (f.endsWith("-all") ? 0 : f.includes("-picks") ? 1 : f.includes("-cat-") ? 2 : 3);
    const list = feeds.slice().sort((a, b) => (a.startsWith("world") - b.startsWith("world")) || order(a) - order(b) || a.localeCompare(b));
    let cp = $("#calPref");
    if (!cp) { cp = document.createElement("p"); cp.id = "calPref"; cp.className = "hint"; $("#subsGrid").before(cp); cp.onclick = (ev) => { if (ev.target.closest("button")) calChoice(null, true); }; }
    const ck = store.get("cal", "");
    cp.innerHTML = `${esc(t("calNow"))} <b>${esc(ck === "apple" ? t("calApple") : ck === "google" ? t("calGoogle") : "—")}</b> <button class="btn" type="button">${esc(t("calChange"))}</button>`;
    $("#subsGrid").innerHTML = list.map((f) => {
      const [r, n] = nameFor(f); const https = feedUrl("cal/" + f + ".ics"); const webcal = https.replace(/^https?:/, "webcal:");
      return `<div class="sub"><span class="tag muted">${esc(r)}</span><b>${esc(n)}</b><div class="row">
        <a class="btn primary" href="${esc(webcal)}">${t("subApple")}</a>
        <a class="btn" href="https://calendar.google.com/calendar/r?cid=${encodeURIComponent(webcal)}" target="_blank" rel="noopener">${t("subGoogle")}</a>
        <button class="btn" data-copy="${esc(https)}">${t("subCopy")}</button></div></div>`;
    }).join("");
    $("#subsGrid").onclick = (ev) => { const b = ev.target.closest("[data-copy]"); if (b) copy(b.dataset.copy); };
    if (CFG.bot) { $("#botCard").hidden = false; $("#botLink").href = "https://t.me/" + CFG.bot; }
  }
  function slugify(s) {
    const tr = { а:"a",б:"b",в:"v",г:"g",д:"d",е:"e",ё:"e",ж:"j",з:"z",и:"i",й:"y",к:"k",л:"l",м:"m",н:"n",о:"o",п:"p",р:"r",с:"s",т:"t",у:"u",ф:"f",х:"h",ц:"c",ч:"c",ш:"s",щ:"s",ъ:"_",ы:"y",ь:"_",э:"e",ю:"u",я:"a" };
    return String(s || "").normalize("NFKD").toLowerCase().split("").map((c) => tr[c] ?? c).join("").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);
  }

  // ------------------------------------------------------------ actions
  function toast(msg) { const el = $("#toast"); el.textContent = msg; el.hidden = false; clearTimeout(toast._t); toast._t = setTimeout(() => (el.hidden = true), 1800); }
  async function copy(text) { try { await navigator.clipboard.writeText(text); toast(t("copied")); } catch (_) { prompt("", text); } }
  function toggleFav(id) {
    if (S.fav.has(id)) { S.fav.delete(id); toast(t("removed")); } else { S.fav.add(id); toast(t("saved")); }
    store.set("fav", [...S.fav]); render(); if (!$("#modal").hidden) openModal(id, true);
  }
  async function share(e) {
    const url = location.origin + location.pathname + "#e=" + encodeURIComponent(e.id);
    const data = { title: L(e, "title"), text: `${L(e, "title")} — ${whenText(e)}, ${place(e)}`, url };
    if (navigator.share) { try { await navigator.share(data); return; } catch (_) { return; } }
    copy(url);
  }
  async function downloadFavIcs() {
    const evs = S.data.events.filter((e) => S.fav.has(e.id) && e.ics);
    const parts = await Promise.all(evs.map((e) => fetch(e.ics).then((r) => r.text()).catch(() => "")));
    const ve = parts.map((p) => (p.match(/BEGIN:VEVENT[\s\S]*?END:VEVENT/) || [""])[0]).filter(Boolean);
    const body = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Afisha Art//RU\r\nX-WR-CALNAME:Избранное\r\n" + ve.join("\r\n") + "\r\nEND:VCALENDAR\r\n";
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([body], { type: "text/calendar" }));
    a.download = "afisha-favorites.ics"; document.body.appendChild(a); a.click(); a.remove();
  }
  function openModal(id, keep) {
    const e = S.data && S.data.events.find((x) => x.id === id); if (!e) return;
    $("#modalBody").innerHTML = detail(e); $("#modal").hidden = false; $("#modal").dataset.id = id;
    if (!keep) history.replaceState(null, "", "#e=" + encodeURIComponent(id));
  }
  function closeModal() { $("#modal").hidden = true; if (location.hash.startsWith("#e=")) history.replaceState(null, "", location.pathname + "#" + S.tab); }

  document.addEventListener("click", (ev) => {
    const tab = ev.target.closest("[data-tab],[data-go]");
    if (tab) { ev.preventDefault(); S.tab = tab.dataset.tab || tab.dataset.go; S.shown = 48; history.replaceState(null, "", "#" + S.tab); render(); window.scrollTo({ top: 0 }); return; }
    const root = ev.target.closest("[data-id]") || (ev.target.closest("#modal") && $("#modal"));
    const id = root && root.dataset.id;
    if (!id) return;
    if (ev.target.closest("[data-cal]")) {
      const e = S.data.events.find((x) => x.id === id);
      if (e) calChoice(e);
      return;
    }
    if (ev.target.closest("[data-fav]")) return toggleFav(id);
    if (ev.target.closest("[data-share]")) return share(S.data.events.find((x) => x.id === id));
    if (ev.target.closest("[data-open]")) return openModal(id);
  });
  $("#closeModal").onclick = closeModal;
  $("#modal").addEventListener("click", (ev) => { if (ev.target.id === "modal") closeModal(); });
  document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeModal(); });
  $("#lang").onclick = () => { S.lang = S.lang === "ru" ? "en" : "ru"; store.set("lang", S.lang); render(); };
  let qt; $("#q").addEventListener("input", (ev) => { clearTimeout(qt); qt = setTimeout(() => { S.q = ev.target.value; S.shown = 48; render(); }, 150); });
  if (CFG.suggest) $("#suggest").href = CFG.suggest; else $("#suggest").hidden = true;

  // install prompt
  let deferred; window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); deferred = e; $("#installBtn").hidden = false; });
  $("#installBtn").onclick = async () => { if (deferred) { deferred.prompt(); deferred = null; $("#installBtn").hidden = true; } };
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(() => {});

  // route
  function route() {
    const h = location.hash.slice(1);
    if (h.startsWith("e=")) { const id = decodeURIComponent(h.slice(2)); const e = S.data && S.data.events.find((x) => x.id === id); if (e) { S.tab = e.region || "ru"; render(); openModal(id, true); } return; }
    if (["ru", "world", "fav", "subs"].includes(h)) S.tab = h;
    render();
  }
  window.addEventListener("hashchange", route);

  // Telegram Mini App (бот открывает сайт с ?tg=1)
  let IN_TG = false;
  function initTelegram() {
    const TGW = window.Telegram && window.Telegram.WebApp;
    if (!TGW || !TGW.initData) return;
    IN_TG = true;
    document.documentElement.classList.add("in-tg");
    try { TGW.ready(); TGW.expand(); TGW.setHeaderColor && TGW.setHeaderColor("#0c0c0f"); TGW.setBackgroundColor && TGW.setBackgroundColor("#0c0c0f"); } catch (_) {}
  }
  const tgReady = new URLSearchParams(location.search).has("tg") ? new Promise((res) => {
    const sc = document.createElement("script"); sc.src = "https://telegram.org/js/telegram-web-app.js";
    sc.onload = () => { initTelegram(); res(); }; sc.onerror = () => res(); document.head.appendChild(sc);
    setTimeout(res, 2500);
  }) : Promise.resolve();
  const firstVisit = !store.get("seen", false);

  render();
  Promise.all([fetch("data/events.json", { cache: "no-cache" }).then((r) => r.json()), tgReady]).then(([d]) => {
    S.data = d;
    const mine = store.get("mine", []).filter((e) => (D(e.end) || D(e.start) || TODAY) >= TODAY);
    store.set("mine", mine);
    d.events = d.events.concat(mine);
    const ids = new Set(d.events.map((e) => e.id)); // чистим избранное от прошедших
    S.fav = new Set([...S.fav].filter((id) => ids.has(id))); store.set("fav", [...S.fav]);
    route();
    // первый экран — выбор города (в Telegram и при первом визите)
    if ((IN_TG || firstVisit) && !location.hash.startsWith("#e=") && S.tab === "ru" && S.place.ru === "all") { const b = $("#placeBtn"); if (b) b.click(); }
    store.set("seen", true);
  }).catch(() => { $("#list").innerHTML = `<div class="empty">Не удалось загрузить данные. Проверьте подключение.</div>`; });
})();
