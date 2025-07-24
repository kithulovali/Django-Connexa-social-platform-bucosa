importScripts('https://www.gstatic.com/firebasejs/9.6.11/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.6.11/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyC78OjRcO9fAzkF2dvgieozf-6WcVWp_1Y",
  authDomain: "bucosa-f357e.firebaseapp.com",
  projectId: "bucosa-f357e",
  storageBucket: "bucosa-f357e.appspot.com",
  messagingSenderId: "33291395764",
  appId: "1:33291395764:web:4515b88070fd1920672de1",
  measurementId: "G-22RMKQ89N1"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: payload.notification.icon
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});