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
      heroRu: "Россия", heroRuSub: "Новая музыка, медиа-арт, выставки, перформанс и театр — во всех городах. Обновляется каждый день.",
      heroWorld: "Мир", heroWorldSub: "Биеннале, фестивали медиаискусства и новой музыки, ярмарки и главные музейные выставки — на год вперёд.",
      heroFav: "Избранное", heroFavSub: "События, отмеченные звёздочкой. Хранятся на этом устройстве.",
      picks: "Выбор редакции", picksSub: "главное в ближайший месяц",
      allPlaces: "Все города", allCountries: "Все страны", morePlaces: "Ещё…", all: "Всё",
      whenAll: "Всё время", whenToday: "Сегодня", whenWeekend: "Выходные", whenWeek: "7 дней", whenMonth: "Месяц",
      search: "Поиск: художник, площадка, композитор…",
      soon: "Ближайшие", live: "Уже идут", liveSub: "по дате закрытия", tba: "Дата уточняется", nothing: "Ничего не нашлось — попробуйте снять фильтры.",
      favEmpty: "Пока пусто. Нажмите ☆ на карточке, чтобы сохранить событие.",
      apple: " Календарь", google: "Google", source: "Источник", share: "Поделиться", more: "Показать ещё",
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
      cats: { music: "Новая музыка", media: "Медиа / диджитал", gallery: "Выставки", performance: "Перформанс", fair: "Ярмарки / фестивали", theatre: "Театр", biennial: "Биеннале" },
      mon: ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"],
      mon1: ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"],
      wd: ["вс","пн","вт","ср","чт","пт","сб"],
    },
    en: {
      brand: "Radar", brandSub: "contemporary art", tabRu: "Russia", tabWorld: "World", tabFav: "Saved", tabSubs: "Subscribe",
      heroRu: "Russia", heroRuSub: "New music, media art, exhibitions, performance and theatre across the country. Updated daily.",
      heroWorld: "World", heroWorldSub: "Biennials, media-art and new-music festivals, fairs and major museum shows — a year ahead.",
      heroFav: "Saved", heroFavSub: "Events you starred. Stored on this device.",
      picks: "Editors' picks", picksSub: "the essentials for the coming month",
      allPlaces: "All cities", allCountries: "All countries", morePlaces: "More…", all: "All",
      whenAll: "Any time", whenToday: "Today", whenWeekend: "Weekend", whenWeek: "7 days", whenMonth: "Month",
      search: "Search: artist, venue, composer…",
      soon: "Coming up", live: "On now", liveSub: "by closing date", tba: "Date TBA", nothing: "Nothing found — try clearing filters.",
      favEmpty: "Nothing yet. Tap ☆ on a card to save an event.",
      apple: " Calendar", google: "Google", source: "Source", share: "Share", more: "Show more",
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
      cats: { music: "New music", media: "Media / digital", gallery: "Exhibitions", performance: "Performance", fair: "Fairs / festivals", theatre: "Theatre", biennial: "Biennials" },
      mon: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
      mon1: ["January","February","March","April","May","June","July","August","September","October","November","December"],
      wd: ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],
    },
  };
  const CAT_HEX = { music: "#7cf2c9", media: "#8f7bff", gallery: "#ffb15c", performance: "#ff6b8b", fair: "#5cc8ff", theatre: "#ff4d3d", biennial: "#e7ff5c" };

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
  function calButtons(e, big) {
    if (!e.ics) return `<span class="btn" aria-disabled="true">${t("tba")}</span>`;
    return `<a class="btn primary" href="${esc(e.ics)}" title="${esc(e.calSummary || "")}">${big ? "" : ""}${t("apple")}</a><a class="btn" href="${esc(e.gcal)}" target="_blank" rel="noopener">${t("google")}</a>`;
  }
  function card(e) {
    const c = t("cats")[e.cat] || e.cat, fav = S.fav.has(e.id);
    return `<article class="card" data-id="${esc(e.id)}">
      <div class="cover" data-open>${cover(e)}<span class="badge b-city">${esc(place(e))}</span>${isLive(e) ? `<span class="badge b-live">${t("liveBadge")}</span>` : ""}${e.isNew ? `<span class="badge b-new">${t("newBadge")}</span>` : ""}<span class="badge b-date">${esc(badge(e))}</span></div>
      <div class="body">
        <span class="tag" style="color:${CAT_HEX[e.cat] || "#fff"}">${esc(c)}${e.tg ? ` <span class="muted">· ${t("fromTg")}</span>` : ""}</span>
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
        <div class="actions">${calButtons(e, true)}<button class="btn star${fav ? " on" : ""}" data-fav>${fav ? "★" : "☆"} ${t("tabFav")}</button><button class="btn" data-share>${t("share")}</button><a class="btn" href="${esc(e.src)}" target="_blank" rel="noopener">${t("source")}: ${esc(e.srcName || "")} ↗</a></div>
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
    if (S.tab === "ru") places.sort((a, b) => (a[0] === "Москва" ? -1 : b[0] === "Москва" ? 1 : b[1] - a[1]));
    const labelOf = (name) => { if (S.lang !== "en") return name; const e = evs.find((x) => x[key] === name); return (e && e[key + "_en"]) || name; };
    const top = places.slice(0, 7), rest = places.slice(7);
    const cur = S.place[S.tab];
    const el = $("#fPlace");
    el.innerHTML = [["all", S.tab === "world" ? t("allCountries") : t("allPlaces")]].concat(top.map(([n, c]) => [n, `${labelOf(n)} · ${c}`]))
      .map(([v, l]) => `<button class="chip${cur === v ? " on" : ""}" data-v="${esc(v)}">${esc(l)}</button>`).join("") +
      (rest.length ? `<select class="chip${rest.some(([n]) => n === cur) ? " on" : ""}" id="morePlaces"><option value="">${t("morePlaces")}</option>${rest.sort((a, b) => labelOf(a[0]).localeCompare(labelOf(b[0]))).map(([n, c]) => `<option value="${esc(n)}"${cur === n ? " selected" : ""}>${esc(labelOf(n))} · ${c}</option>`).join("")}</select>` : "");
    el.onclick = (ev) => { const b = ev.target.closest("button.chip"); if (b) setPlace(b.dataset.v); };
    const sel = $("#morePlaces"); if (sel) sel.onchange = () => sel.value && setPlace(sel.value);
    const cats = Object.keys(t("cats")).filter((k) => evs.some((e) => e.cat === k));
    chips($("#fCat"), [["all", t("all")]].concat(cats.map((k) => [k, t("cats")[k], CAT_HEX[k]])), S.cat, (v) => { S.cat = v; S.shown = 48; render(); });
    chips($("#fWhen"), [["all", t("whenAll")], ["today", t("whenToday")], ["weekend", t("whenWeekend")], ["week", t("whenWeek")], ["month", t("whenMonth")]], S.when, (v) => { S.when = v; S.shown = 48; render(); });
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
    const list = base.filter((e) => (cur === "all" || e[key] === cur) && (S.cat === "all" || e.cat === S.cat) && inWhen(e) &&
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

  render();
  fetch("data/events.json", { cache: "no-cache" }).then((r) => r.json()).then((d) => {
    S.data = d;
    const ids = new Set(d.events.map((e) => e.id)); // чистим избранное от прошедших
    S.fav = new Set([...S.fav].filter((id) => ids.has(id))); store.set("fav", [...S.fav]);
    route();
  }).catch(() => { $("#list").innerHTML = `<div class="empty">Не удалось загрузить данные. Проверьте подключение.</div>`; });
})();
