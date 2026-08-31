const CACHE = "beike-assistant-v3";
const STATIC_URLS = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/js/components.js",
  "/static/manifest.json",
];

const API_CACHE = "beike-api-v3";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((k) => k !== CACHE && k !== API_CACHE)
          .map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  event.respondWith(networkFirst(request, CACHE));
});

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok && cacheName) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (request.destination === "style" || request.destination === "script" || request.destination === "font" || request.destination === "image") {
      return new Response("", { status: 503 });
    }
    return new Response(JSON.stringify({ success: false, message: "离线模式，无法访问" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}