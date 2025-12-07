# Быстрый старт - Nail Salon Booking System

## 🚀 Развертывание за 5 минут

### Шаг 1: Клонирование проекта

```bash
git clone <your-repo-url>
cd nail-salon-booking
```

### Шаг 2: Настройка окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env и установите безопасные пароли
nano .env
```

**Минимальные настройки для production:**
```env
MONGO_ROOT_PASSWORD=your_secure_password_here
JWT_SECRET=your_very_long_secret_key_minimum_32_characters
ADMIN_PASSWORD=your_admin_password
REACT_APP_BACKEND_URL=https://your-domain.com
```

### Шаг 3: Запуск

```bash
# Автоматическое развертывание
chmod +x deploy.sh
./deploy.sh

# ИЛИ вручную
docker compose build
docker compose up -d
```

### Шаг 4: Инициализация данных

```bash
# Создайте начальные услуги и расписание
python3 init_data.py
```

## 📱 Доступ к приложению

- **Сайт**: http://localhost:3000
- **API**: http://localhost:8001
- **Админка**: http://localhost:3000/admin/login
  - Логин: `admin`
  - Пароль: из `.env` файла

## 🔧 Управление

```bash
# Просмотр логов
docker compose logs -f

# Остановка
docker compose down

# Перезапуск
docker compose restart

# Обновление после изменений
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 🌐 Production развертывание

### С Nginx и SSL

1. Установите Nginx:
```bash
sudo apt install nginx certbot python3-certbot-nginx
```

2. Создайте конфигурацию Nginx:
```bash
sudo nano /etc/nginx/sites-available/nail-salon
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. Активируйте конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/nail-salon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. Установите SSL:
```bash
sudo certbot --nginx -d yourdomain.com
```

## 🔐 Безопасность

1. ✅ Измените все пароли по умолчанию
2. ✅ Используйте сильный JWT_SECRET (минимум 32 символа)
3. ✅ Настройте firewall
4. ✅ Используйте HTTPS в production
5. ✅ Настройте регулярные бэкапы MongoDB

## 📦 Резервное копирование

```bash
# Создание бэкапа
docker compose exec mongodb mongodump --out /data/backup
docker cp nail-salon-mongodb:/data/backup ./backup-$(date +%Y%m%d)

# Восстановление
docker compose exec mongodb mongorestore /data/backup
```

## 🆘 Помощь

Проблемы? Проверьте логи:
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs mongodb
```

Полная документация: [README_DEPLOY.md](README_DEPLOY.md)
