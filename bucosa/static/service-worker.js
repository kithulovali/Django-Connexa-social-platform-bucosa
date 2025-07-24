// Listen for push events and show notifications
self.addEventListener('push', function(event) {
  event.waitUntil((async () => {
    let data = {};
    if (event.data) {
      try {
        data = event.data.json();
      } catch (e) {
        let rawText = null;
        try {
          rawText = await event.data.text();
        } catch (err) {
          rawText = null;
        }
        // Try to extract title, body, and URL from the raw text if possible
        let url = '/';
        let title = 'Bucosa Notification';
        let body = rawText || 'You have a new notification!';
        if (rawText) {
          // Try to extract a URL
          const urlMatch = rawText.match(/https?:\/\/[^\s]+/);
          if (urlMatch) url = urlMatch[0];
          // Try to extract a title (e.g. "Title: ...")
          const titleMatch = rawText.match(/title\s*:\s*([^\n]+)/i);
          if (titleMatch) title = titleMatch[1].trim();
          // Try to extract a body (e.g. "body: ...")
          const bodyMatch = rawText.match(/body\s*:\s*([^\n]+)/i);
          if (bodyMatch) body = bodyMatch[1].trim();
        }
        data = {
          title: title,
          body: body,
          url: url
        };
        // Log error for debugging
        console.error('Push payload was not valid JSON:', rawText);
      }
    } else {
      data = {
        title: 'Bucosa Notification',
        body: 'You have a new notification!',
        url: '/'
      };
    }
    const title = data.title || 'Bucosa Notification';
    const options = {
      body: data.body || 'You have a new notification!',
      icon: '/static/img/pwa-icon.png',
      badge: '/static/img/pwa-icon.png',
      data: data.url || '/',
    };
    await self.registration.showNotification(title, options);
  })());
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data || '/';
  event.waitUntil((async () => {
    const allClients = await clients.matchAll({ type: 'window', includeUncontrolled: true });
    let found = false;
    for (const client of allClients) {
      // If the url is already open, focus it
      if (client.url.includes(url) && 'focus' in client) {
        await client.focus();
        found = true;
        break;
      }
    }
    if (!found && clients.openWindow) {
      await clients.openWindow(url);
    }
  })());
});
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('bucosa-cache-v1').then(cache => {
      // Only cache files that exist
      return cache.addAll([
        '/',
        '/static/manifest.json',
        // '/static/img/pwa-icon.png', // Uncomment if you want to cache the icon and it exists
        // Add more static assets as needed, but make sure they exist
      ]).catch(err => {
        console.error('Service Worker cache addAll error:', err);
      });
    })
  );
self.addEventListener('fetch', event => {
  // Fallback for favicon.ico to avoid 404 errors
  if (event.request.url.endsWith('favicon.ico')) {
    event.respondWith(new Response('', { status: 204 }));
    return;
  }
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
