/* 서비스 워커: 한 번 열고 나면 인터넷이 없어도(새로고침해도) 사이트가 열리게 해 준다.
   - 이 사이트의 파일(index.html, style.css, py 파일 등): 인터넷이 되면 늘 새로 받아 저장해 두고(고친 내용이 바로 반영),
     인터넷이 안 되면 저장해 둔 것을 쓴다.
   - 주소에 버전이 들어 있는 바깥 파일(PyScript, 파이썬 엔진 Pyodide): 한 번 받으면 저장해 둔 것을 쓴다.
   - 글꼴은 저장하지 않는다. 인터넷 없이 열면 글자만 컴퓨터에 있는 기본 글꼴로 보인다.
   index.html에서 PyScript 버전을 올리면 아래 CACHE의 숫자도 하나 올려 주세요 (예전에 저장한 파일이 지워진다). */
const CACHE = "rsa-booth-v1";
const FONTS = ["fonts.googleapis.com", "fonts.gstatic.com", "/pretendard@"]; // 주소에 이것이 들어 있으면 글꼴
const isFont = (url) => FONTS.some((part) => url.includes(part));

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      if (name !== CACHE) await caches.delete(name);
    }
    await self.clients.claim(); // 처음 연 페이지도 바로 맡는다
  })());
});

// 서비스 워커가 생기기 전에 받은 파일(처음 접속)도 저장해 달라는 부탁 — main.py의 save_for_offline
self.addEventListener("message", (event) => {
  if (Array.isArray(event.data)) event.waitUntil(saveAll(event.data));
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || !request.url.startsWith("http") || isFont(request.url)) return;
  if (request.cache === "only-if-cached" && request.mode !== "same-origin") return;
  const mine = new URL(request.url).origin === self.location.origin;
  event.respondWith(mine ? networkFirst(event) : cacheFirst(event));
});

async function networkFirst(event) {
  const request = event.request;
  try {
    const response = await fetch(request);
    if (response.ok) event.waitUntil(save(request, response.clone()));
    return response;
  } catch (error) { // 인터넷이 안 되면 저장해 둔 것
    const cache = await caches.open(CACHE);
    const saved = await cache.match(request, { ignoreSearch: true, ignoreVary: true })
      || (request.mode === "navigate" && await cache.match("./"));
    if (saved) return saved;
    throw error;
  }
}

async function cacheFirst(event) {
  const request = event.request;
  const saved = await caches.match(request, { ignoreVary: true });
  if (saved) return saved;
  const response = await fetch(request);
  if (response.ok) event.waitUntil(save(request, response.clone()));
  return response;
}

async function save(request, response) {
  try {
    await (await caches.open(CACHE)).put(request, response);
  } catch (error) { /* 저장 공간이 모자라는 등 — 다음에 다시 */ }
}

async function saveAll(urls) {
  const cache = await caches.open(CACHE);
  await Promise.all(urls.map(async (url) => {
    if (!url.startsWith("http") || isFont(url) || await cache.match(url, { ignoreVary: true })) return;
    try {
      const response = await fetch(url);
      if (response.ok) await cache.put(url, response);
    } catch (error) { /* 못 받은 파일은 다음에 열 때 저장된다 */ }
  }));
}
