// Poll unread messages count and update badge

function pollUnreadMessagesBadge() {
  function updateBadge(count) {
    // Desktop
    const desktopBadge = document.getElementById('desktop-message-badge');
    if (desktopBadge) {
      if (count > 0) {
        desktopBadge.textContent = count;
        desktopBadge.style.display = 'inline-flex';
      } else {
        desktopBadge.style.display = 'none';
      }
    }
    // Mobile
    const mobileBadge = document.getElementById('mobile-message-badge');
    if (mobileBadge) {
      if (count > 0) {
        mobileBadge.textContent = count;
        mobileBadge.style.display = 'inline-flex';
      } else {
        mobileBadge.style.display = 'none';
      }
    }
  }
  function fetchCount() {
    fetch('/api/unread_messages_count/', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => updateBadge(data.unread_messages_count))
      .catch(() => {});
  }
  fetchCount();
  setInterval(fetchCount, 10000);
}

if (window.USER_IS_AUTHENTICATED) {
  document.addEventListener('DOMContentLoaded', pollUnreadMessagesBadge);
  document.addEventListener('DOMContentLoaded', pollUnreadNotificationsBadge);
}

// Poll unread notifications count and update badge

function pollUnreadNotificationsBadge() {
  function updateNotifBadge(count) {
    // Desktop
    const desktopBadge = document.getElementById('desktop-notif-badge');
    if (desktopBadge) {
      if (count > 0) {
        desktopBadge.textContent = count;
        desktopBadge.style.display = 'inline-flex';
      } else {
        desktopBadge.style.display = 'none';
      }
    }
    // Mobile
    const mobileBadge = document.getElementById('mobile-notif-badge');
    if (mobileBadge) {
      if (count > 0) {
        mobileBadge.textContent = count;
        mobileBadge.style.display = 'inline-flex';
      } else {
        mobileBadge.style.display = 'none';
      }
    }
  }
  function fetchNotifCount() {
    fetch('/notifications/api/unread_count/', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => updateNotifBadge(data.unread_notifications_count))
      .catch(() => {});
  }
  fetchNotifCount();
  setInterval(fetchNotifCount, 10000);
}

      // Toast function
      function showToast(msg, type = 'info') {
        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.className = `bucosa-toast${type === 'error' ? ' bucosa-toast-error' : ''}`;
        Object.assign(toast.style, {
          position: 'fixed',
          bottom: '30px',
          right: '30px',
          background: type === 'info' ? '#2563eb' : '#e53e3e',
          color: 'white',
          padding: '16px 24px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          zIndex: 9999,
          fontSize: '16px',
          transition: 'opacity 0.3s'
        });
        document.body.appendChild(toast);
        setTimeout(() => { toast.style.opacity = 0; }, 3000);
        setTimeout(() => { toast.remove(); }, 3500);
      }

      // Play notification sound
      function playNotificationSound() {
        const audio = new Audio('/static/sounds/notify.mp3');
        audio.play();
      }

      // Badge and dropdown update
      function updateNotificationBadge() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
          let count = parseInt(badge.textContent) || 0;
          badge.textContent = count + 1;
          badge.style.display = 'inline-block';
        }
      }

      function prependNotificationDropdown(data) {
        const dropdown = document.getElementById('notification-dropdown');
        if (dropdown) {
          const item = document.createElement('a');
          item.className = 'dropdown-item block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100';
          item.href = data.url || '#';
          item.textContent = data.message || 'New notification';
          dropdown.prepend(item);
        }
      }

      // CSRF utility
      function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }

      // WebSocket reconnect logic
      function setupNotificationSocket() {
        // Only establish WebSocket connection for authenticated users
        if (window.USER_IS_AUTHENTICATED) {
          let ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
          let ws_path = ws_scheme + '://' + window.location.host + "/ws/notifications/";
          let notificationSocket = new WebSocket(ws_path);

          notificationSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            showToast(data.message || "New notification", 'info');
            playNotificationSound();
            updateNotificationBadge();
            prependNotificationDropdown(data);
          };

          notificationSocket.onclose = function(e) {
            console.error('Notification socket closed unexpectedly, reconnecting...');
            setTimeout(setupNotificationSocket, 2000);
          };
        }
      }
      setupNotificationSocket();

      // Dropdown show/hide and mark as read
      const bell = document.getElementById('notificationDropdown');
      const dropdown = document.getElementById('notification-dropdown');
      bell.addEventListener('click', function(e) {
        e.stopPropagation();
        if (dropdown.style.display === 'none' || dropdown.style.display === '') {
          dropdown.style.display = 'block';
          // Mark as read
          fetch('/notifications/mark_read/', {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')}
          });
          const badge = document.getElementById('notification-badge');
          if (badge) {
            badge.textContent = '0';
            badge.style.display = 'none';
          }
        } else {
          dropdown.style.display = 'none';
        }
      });
      // Hide dropdown when clicking outside
      document.addEventListener('click', function(e) {
        if (!bell.contains(e.target) && !dropdown.contains(e.target)) {
          dropdown.style.display = 'none';
        }
      });
    