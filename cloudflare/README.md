# Посредник для поиска через Яндекс (Cloudflare Worker)

Нужен только для личного поиска через Яндекс (работает в России без VPN). Бесплатно на тарифе Cloudflare Free.

1. Зарегистрируйтесь на dash.cloudflare.com (бесплатно).
2. Workers & Pages → Create → **Create Worker** → имя `radar-proxy` → Deploy.
3. Edit code → удалите всё и вставьте содержимое `worker.js` → **Deploy**.
4. Скопируйте адрес вида `https://radar-proxy.<ваш-ник>.workers.dev`.
5. В репозитории откройте `site/config.js` → вставьте адрес в `proxy: "..."` → Commit.

Через пару минут в «Найти больше» появится вкладка «Яндекс». Ключи пользователей посредник не сохраняет;
поиск и YandexGPT оплачиваются со счёта Yandex Cloud каждого пользователя.
