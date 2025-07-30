importScripts('https://www.gstatic.com/firebasejs/10.11.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.11.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAsXHxxto0D-0nZ2I7sIhHFDjCAgurUoZM",
  authDomain: "bucosa-5ccde.firebaseapp.com",
  projectId: "bucosa-5ccde",
  storageBucket: "bucosa-5ccde.appspot.com",
  messagingSenderId: "981676237571",
  appId: "1:981676237571:web:1a7445524217e5ae917f36",
  measurementId: "G-XNJBM8KB53"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: '/static/img/pwa-icon.png'
  });
});