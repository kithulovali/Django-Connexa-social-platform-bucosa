    
      const firebaseConfig = {
        apiKey: "AIzaSyAsXHxxto0D-0nZ2I7sIhHFDjCAgurUoZM",
        authDomain: "bucosa-5ccde.firebaseapp.com",
        projectId: "bucosa-5ccde",
        storageBucket: "bucosa-5ccde.appspot.com",
        messagingSenderId: "981676237571",
        appId: "1:981676237571:web:1a7445524217e5ae917f36",
        measurementId: "G-XNJBM8KB53"
      };
      firebase.initializeApp(firebaseConfig);

      const messaging = firebase.messaging();

      function sendTokenToBackend(token) {
        if (localStorage.getItem('fcm_token') !== token) {
          fetch('/save_fcm_token/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'token=' + encodeURIComponent(token)
          }).then(() => {
            localStorage.setItem('fcm_token', token);
          });
        }
      }

      function getAndSendToken() {
        Notification.requestPermission().then((permission) => {
          if (permission === 'granted') {
            messaging.getToken({ vapidKey: 'BIrGRQ1nsd0Cf7Fpmd-qMKhkqLMUaXXXpBUpkPc908eBgSN3ApVrSkQuLvS6Phz8UVLT3QlYSZ0RyIQBjbAuhFc' })
              .then((token) => {
                if (token) {
                  sendTokenToBackend(token);
                } else {
                  console.log('No registration token available.');
                }
              })
              .catch((err) => {
                console.log('Unable to get token.', err);
              });
          } else {
            console.log('Notification permission not granted.');
          }
        });
      }

      window.addEventListener('load', getAndSendToken);

      messaging.onTokenRefresh(() => {
        messaging.getToken({ vapidKey: 'BIrGRQ1nsd0Cf7Fpmd-qMKhkqLMUaXXXpBUpkPc908eBgSN3ApVrSkQuLvS6Phz8UVLT3QlYSZ0RyIQBjbAuhFc' })
          .then((refreshedToken) => {
            sendTokenToBackend(refreshedToken);
          })
          .catch((err) => {
            console.log('Unable to retrieve refreshed token ', err);
          });
      });

      messaging.onMessage((payload) => {
        alert('Push notification: ' + payload.notification.title + ' - ' + payload.notification.body);
      });
    