// Посредник «Радара» для личного поиска через Яндекс (работает в России без VPN).
// Браузер не может напрямую обращаться к API Yandex Cloud (CORS), поэтому запрос идёт через этот Worker.
// Ключ пользователя приходит в запросе, используется один раз и НИГДЕ не сохраняется.
// Оплата поиска и YandexGPT — со счёта Yandex Cloud самого пользователя.

const ALLOWED_ORIGINS = ["https://doublebasskakov.github.io"]; // адрес сайта; добавьте свой домен, если появится

function cors(origin) {
  const ok = ALLOWED_ORIGINS.includes(origin);
  return {
    "Access-Control-Allow-Origin": ok ? origin : ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function decodeB64Utf8(b64) {
  const bin = atob(b64);
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  return new TextDecoder("utf-8").decode(bytes);
}

function parseResults(xml) {
  const out = [];
  const docs = xml.split("<doc ").slice(1);
  for (const d of docs) {
    const strip = (s) => (s || "").replace(/<[^>]+>/g, "").replace(/&quot;/g, '"').replace(/&amp;/g, "&").trim();
    const url = (d.match(/<url>([\s\S]*?)<\/url>/) || [])[1];
    const title = strip((d.match(/<title>([\s\S]*?)<\/title>/) || [])[1]);
    const passages = [...d.matchAll(/<passage>([\s\S]*?)<\/passage>/g)].map((m) => strip(m[1])).join(" … ");
    if (url) out.push({ url, title, text: passages.slice(0, 600) });
  }
  return out;
}

async function yandexSearch(apiKey, folderId, queryText) {
  const r = await fetch("https://searchapi.api.cloud.yandex.net/v2/web/search", {
    method: "POST",
    headers: { Authorization: `Api-Key ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      query: { searchType: "SEARCH_TYPE_RU", queryText, familyMode: "FAMILY_MODE_MODERATE" },
      groupSpec: { groupMode: "GROUP_MODE_DEEP", groupsOnPage: "15", docsInGroup: "1" },
      folderId, responseFormat: "FORMAT_XML", l10n: "LOCALIZATION_RU",
    }),
  });
  const j = await r.json();
  if (!r.ok) throw new Error("Yandex Search: " + (j.message || r.status));
  return parseResults(decodeB64Utf8(j.rawData || ""));
}

async function yandexGpt(apiKey, folderId, text) {
  const r = await fetch("https://llm.api.cloud.yandex.net/foundationModels/v1/completion", {
    method: "POST",
    headers: { Authorization: `Api-Key ${apiKey}`, "x-folder-id": folderId, "Content-Type": "application/json" },
    body: JSON.stringify({
      modelUri: `gpt://${folderId}/yandexgpt/latest`,
      completionOptions: { stream: false, temperature: 0.2, maxTokens: "4000" },
      messages: [{ role: "user", text }],
    }),
  });
  const j = await r.json();
  if (!r.ok) throw new Error("YandexGPT: " + (j.message || r.status));
  return j.result?.alternatives?.[0]?.message?.text || "";
}

export default {
  async fetch(request) {
    const origin = request.headers.get("Origin") || "";
    const headers = cors(origin);
    if (request.method === "OPTIONS") return new Response(null, { headers });
    if (request.method !== "POST" || new URL(request.url).pathname !== "/search") return new Response("Not found", { status: 404, headers });
    if (!ALLOWED_ORIGINS.includes(origin)) return new Response("Forbidden", { status: 403, headers });
    try {
      const { apiKey, folderId, queries, prompt } = await request.json();
      if (!apiKey || !folderId || !Array.isArray(queries) || !prompt) throw new Error("bad request");
      const results = [];
      for (const q of queries.slice(0, 4)) results.push(...(await yandexSearch(apiKey, folderId, String(q).slice(0, 300))));
      const seen = new Set(); const uniq = results.filter((x) => !seen.has(x.url) && seen.add(x.url)).slice(0, 40);
      const context = uniq.map((x, i) => `[${i}] ${x.title}\n${x.url}\n${x.text}`).join("\n\n");
      const text = await yandexGpt(apiKey, folderId, `${prompt}\n\nРезультаты поиска (используй только их, src бери из URL):\n${context}`);
      return new Response(JSON.stringify({ text, found: uniq.length }), { headers: { ...headers, "Content-Type": "application/json" } });
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e.message || e) }), { status: 400, headers: { ...headers, "Content-Type": "application/json" } });
    }
  },
};
