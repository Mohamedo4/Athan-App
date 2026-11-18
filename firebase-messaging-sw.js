importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');
firebase.initializeApp({ apiKey: "AIzaSyC_oAsF6b9sjXHzD0gessQCknqJROjd5c", projectId: "athan-app-e3dec", messagingSenderId: "945830754340", appId: "1:945830754340:web:3ef17560a0bd1a916a00b1" });
const messaging = firebase.messaging();
messaging.onBackgroundMessage((payload) => {
  self.registration.showNotification(payload.notification.title, { body: payload.notification.body });
});