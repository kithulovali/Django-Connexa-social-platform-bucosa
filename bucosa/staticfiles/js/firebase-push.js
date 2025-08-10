// static/js/firebase-push.js

const firebaseConfig = window.FIREBASE_CONFIG;
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function sendTokenToBackend(token) {
  if (localStorage.getItem('fcm_token') !== token) {
    fetch('/save_fcm_token/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken')  // only if CSRF is required
      },
      body: 'token=' + encodeURIComponent(token)
    }).then(() => {
      localStorage.setItem('fcm_token', token);
    }).catch(err => {
      console.error('Failed to send token to backend:', err);
    });
  }
}

function getAndSendToken() {
  Notification.requestPermission().then((permission) => {
    if (permission === 'granted') {
      navigator.serviceWorker.ready.then((registration) => {
        messaging.getToken({
          vapidKey: window.FIREBASE_VAPID_KEY,
          serviceWorkerRegistration: registration
        })
        .then((token) => {
          if (token) {
            console.log('FCM Token:', token);
            sendTokenToBackend(token);
          } else {
            console.log('No registration token available.');
          }
        })
        .catch((err) => {
          console.error('Unable to get token.', err);
        });
      });
    } else {
      console.log('Notification permission not granted.');
    }
  });
}

if (window.USER_IS_AUTHENTICATED === true) {
  getAndSendToken();
}
