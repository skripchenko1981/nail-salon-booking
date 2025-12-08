# 🚀 Налаштування Nail Studio

Цей документ містить інструкції по налаштуванню системи бронювання для салону краси з підтримкою кількох майстрів.

## 📋 Зміст

1. [Вимоги](#вимоги)
2. [Налаштування Backend](#налаштування-backend)
3. [Налаштування Frontend](#налаштування-frontend)
4. [Ініціалізація Бази Даних](#ініціалізація-бази-даних)
5. [Інтеграції (опціонально)](#інтеграції-опціонально)

---

## 🔧 Вимоги

- Python 3.8+
- Node.js 16+
- MongoDB 4.4+
- yarn (для frontend)

---

## 🖥️ Налаштування Backend

### 1. Створення файлу конфігурації

```bash
cd backend
cp .env.example .env
```

### 2. Редагування `.env`

Відкрийте `backend/.env` та налаштуйте змінні:

```bash
# MongoDB - вже налаштовано платформою
MONGO_URL="mongodb://localhost:27017"
DB_NAME="nail_salon"

# CORS
CORS_ORIGINS="*"

# JWT Secret - ВАЖЛИВО: Змініть на безпечний ключ!
JWT_SECRET="your-super-secret-jwt-key-change-this"

# Credentials адміністратора
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="your-secure-password"

# Telegram (опціонально)
TELEGRAM_BOT_TOKEN=""
ADMIN_TELEGRAM_ID=""
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Запуск сервера

Сервер автоматично запускається через supervisor на порту 8001.

---

## 🎨 Налаштування Frontend

### 1. Створення файлу конфігурації

```bash
cd frontend
cp .env.example .env
```

### 2. Редагування `.env`

```bash
# URL backend'у - вже налаштовано платформою
REACT_APP_BACKEND_URL=https://your-domain.com

# WebSocket
WDS_SOCKET_PORT=443

# Feature flags
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

### 3. Встановлення залежностей

```bash
yarn install
```

### 4. Запуск

Frontend автоматично запускається через supervisor на порту 3000.

---

## 🗄️ Ініціалізація Бази Даних

### Автоматична ініціалізація (рекомендовано)

Скрипт створить 2 тестових майстри з графіками роботи та послугами:

```bash
cd backend
python3 init_db.py
```

**Створені тестові майстри:**
- Email: `olena@example.com` | Пароль: `master123`
- Email: `maria@example.com` | Пароль: `master123`

**Admin:**
- Login: `admin` | Пароль: `admin123` (або ваш з .env)

### Ручна ініціалізація

Якщо потрібно створити майстрів вручну:

1. Увійдіть як адміністратор: `/admin/login`
2. Перейдіть до розділу "Майстри"
3. Створіть нових майстрів (графік роботи створюється автоматично)

---

## 🔌 Інтеграції (опціонально)

### Telegram Notifications

1. Створіть бота через [@BotFather](https://t.me/BotFather)
2. Отримайте токен бота
3. Отримайте свій Telegram ID через [@userinfobot](https://t.me/userinfobot)
4. Додайте в `backend/.env`:

```bash
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
ADMIN_TELEGRAM_ID="123456789"
```

### Twilio SMS

1. Зареєструйтесь на [Twilio](https://www.twilio.com)
2. Отримайте Account SID, Auth Token та Phone Number
3. Додайте в `backend/.env`:

```bash
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_auth_token"
TWILIO_PHONE_NUMBER="+380XXXXXXXXX"
```

---

## 🚀 Швидкий Старт (Локально)

```bash
# 1. Клонувати репозиторій
git clone <repo-url>
cd nail-studio

# 2. Backend
cd backend
cp .env.example .env
# Відредагуйте .env
pip install -r requirements.txt
python3 init_db.py
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 3. Frontend (в іншому терміналі)
cd frontend
cp .env.example .env
# Відредагуйте .env
yarn install
yarn start
```

Відкрийте браузер:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/docs

---

## 📚 Структура Проекту

```
/app
├── backend/
│   ├── server.py           # Головний FastAPI сервер
│   ├── init_db.py          # Скрипт ініціалізації БД
│   ├── telegram_bot.py     # Telegram інтеграція
│   ├── sms_service.py      # SMS інтеграція
│   ├── .env                # Конфігурація backend
│   └── requirements.txt    # Python залежності
│
├── frontend/
│   ├── src/
│   │   ├── pages/          # Сторінки React
│   │   ├── components/     # React компоненти
│   │   └── utils/          # Утиліти
│   ├── .env                # Конфігурація frontend
│   └── package.json        # Node залежності
│
└── .env.example            # Приклад конфігурації
```

---

## 🔐 Безпека

**ВАЖЛИВО перед Production:**

1. ✅ Змініть `JWT_SECRET` на сильний випадковий ключ
2. ✅ Змініть `ADMIN_PASSWORD` на безпечний пароль
3. ✅ Налаштуйте CORS тільки для ваших доменів
4. ✅ Використовуйте HTTPS
5. ✅ Регулярно оновлюйте залежності
6. ✅ НЕ комітьте файли `.env` в git

---

## 🆘 Типові Проблеми

### "На цю дату немає доступних слотів"

**Причина:** Майстер не має графіку роботи

**Рішення:**
```bash
cd backend
python3 init_db.py
```

### "Помилка оновлення запису"

**Причина:** Токен не знайдено

**Рішення:** Перелогіньтесь у систему

### Backend не запускається

**Причина:** Не встановлено залежності

**Рішення:**
```bash
cd backend
pip install -r requirements.txt
```

---

## 📞 Підтримка

Якщо у вас виникли питання:
1. Перевірте логи: `tail -f /var/log/supervisor/backend.*.log`
2. Перевірте статус: `sudo supervisorctl status`
3. Перезапустіть сервіси: `sudo supervisorctl restart all`

---

## 📝 Ліцензія

Цей проект розроблено для салону краси з multi-master системою бронювання.
