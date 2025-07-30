# Django-Connexa-social-platform-bucosa
# Connexa Social Platform (Bucosa)

Connexa is a Django-based social platform designed to connect users through posts, comments, groups, events, and real-time notifications. It supports user authentication, push notifications, group chats, and a modern PWA experience.

---

## 📄 Project Description

Connexa Social Platform (Bucosa) is a feature-rich social networking application built with Django. It allows users to:
- Register, log in, and manage profiles
- Create and join groups
- Post updates, comment, and mention other users
- Receive real-time and push notifications (via FCM)
- Chat in groups and private messages (using Django Channels & Redis)
- Browse events and save favorite posts
- Enjoy a Progressive Web App (PWA) experience

The backend is powered by Django, PostgreSQL (Neon), and Redis (Upstash), and is ready for cloud deployment (Railway).

---

## 📁 Project Structure

```
bucosa/
│
├── activities/         # Posts, comments, events, and related views/models
├── fellowship/         # Group and community features
├── government/         # Admin and moderation features
├── notifications/      # Notification system and push logic
├── users/              # User profiles, authentication, and social features
│
├── bucosa/             # Project settings, URLs, ASGI/WSGI config
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
│
├── templates/          # HTML templates
├── static/             # Static files (CSS, JS, images)
├── manage.py
└── requirements.txt
```

---

## 🚀 Installation & Setup

### 1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/Django-Connexa-social-platform-bucosa.git
cd Django-Connexa-social-platform-bucosa
```

### 2. **Create and Activate a Virtual Environment**
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Set Environment Variables**

Create a `.env` file in the root directory and add:
```
REQUEST FOR  THESE INFORMATION 
DJANGO_SECRET_KEY
DATABASE_URL
REDIS_URL
FIREBASE_CREDENTIALS
DEBUG=True
```

### 5. **Apply Migrations**
```bash
python manage.py migrate
```

### 6. **Collect Static Files**
```bash
python manage.py collectstatic --noinput
```

### 7. **Run the Development Server**
```bash
python manage.py runserver
```

---

## 🌐 Deployment

- Ready for deployment on [Railway](https://railway.app/), [Heroku](https://heroku.com/), or any cloud platform.
- Set all environment variables in your deployment dashboard.
- Use Gunicorn or Daphne for production.

---
...

---

## 🤝 Sponsor

<p align="center">
  <a href="https://railway.app/" target="_blank" title="Railway">
    <img src="https://railway.app/brand/logo-light.png" alt="Railway Logo" width="120"/>
  </a>
</p>

<p align="center">
  <b>
    <a href="https://railway.app/" target="_blank">Railway</a>
  </b>
</p>

<p align="center">
  <sub>
    Railway: Cloud Infrastructure Made Easy
  </sub>
</p>

---

---

## 📬 Contact Information

**Project Maintainer:**  
Goffart kithulovali Jean Marc  

[![Email](https://img.shields.io/badge/Email-kithulovalibin@gmail.com-blue?logo=gmail&logoColor=white&style=for-the-badge)](mailto:kithulovalibin@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-kithulovali-black?logo=github&logoColor=white&style=for-the-badge)](https://github.com/kithulovali)

**Contributor:**  
Irunva Mapendo Joel  
[![Email](https://img.shields.io/badge/Email-joelmapendo243@gmail.com-blue?logo=gmail&logoColor=white&style=for-the-badge)](mailto:joelmapendo243@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-JoelMapendo-black?logo=github&logoColor=white&style=for-the-badge)](https://github.com/JoelMapendo)

---

*Feel free to open issues or pull requests for improvements!*
