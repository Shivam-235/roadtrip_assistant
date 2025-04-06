self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('trip-bot-cache').then((cache) => {
            return cache.addAll([
              '/',
              '/static/js/chat.js',
              '/static/css/style.css',
              '/static/icon-192.png',
              '/static/icon-512.png'
            ]);
      }));
  });
  
  self.addEventListener('fetch', (e) => {
    e.respondWith(
      caches.match(e.request).then((res) => res || fetch(e.request))
    );
  });
  