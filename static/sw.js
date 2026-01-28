const CACHE_NAME = 'portfolio-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/digital_alchemy.css',
  '/static/manifest.json',
  '/offline.html',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install Event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
});

// Activate Event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

// Fetch Event (Network First, fallback to cache)
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests like Google Analytics
  if (!event.request.url.startsWith(self.location.origin) && !event.request.url.includes('cdnjs') && !event.request.url.includes('fonts')) {
      return;
  }
  
  // Skip POST requests
  if (event.request.method !== 'GET') {
      return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Check if we received a valid response
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }

        // Clone the response
        const responseToCache = response.clone();

        caches.open(CACHE_NAME)
          .then((cache) => {
            cache.put(event.request, responseToCache);
          });

        return response;
      })
      .catch(() => {
        return caches.match(event.request)
            .then((response) => {
                if (response) {
                    return response;
                }
                // Return offline page if navigation fails
                if (event.request.mode === 'navigate') {
                    return caches.match('/offline.html');
                }
            });
      })
  );
});
