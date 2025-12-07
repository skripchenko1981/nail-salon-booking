# Развертывание проекта на Ubuntu сервере с Docker

## Предварительные требования

- Ubuntu Server 20.04 или выше
- Docker Engine 20.10+
- Docker Compose 2.0+
- Минимум 2GB RAM
- Минимум 10GB свободного места на диске

## 1. Установка Docker и Docker Compose

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление официального GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавление пользователя в группу docker (опционально)
sudo usermod -aG docker $USER
newgrp docker

# Проверка установки
docker --version
docker compose version
```

## 2. Подготовка проекта

```bash
# Клонирование репозитория (или загрузка файлов)
git clone <your-repo-url>
cd nail-salon-booking

# Создание .env файла
cp .env.example .env

# Редактирование .env файла
nano .env
```

### Важные параметры в .env:

```env
# MongoDB
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=ВАШ_СЛОЖНЫЙ_ПАРОЛЬ
DB_NAME=nail_salon

# Backend
JWT_SECRET=ВАШ_ОЧЕНЬ_СЕКРЕТНЫЙ_КЛЮЧ_МИНИМУМ_32_СИМВОЛА
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ВАШ_АДМИН_ПАРОЛЬ
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Frontend
REACT_APP_BACKEND_URL=http://localhost:8001
FRONTEND_PORT=3000
```

## 3. Сборка и запуск

```bash
# Сборка образов
docker compose build

# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f

# Просмотр логов конкретного сервиса
docker compose logs -f backend
docker compose logs -f frontend
```

## 4. Инициализация данных

После первого запуска выполните скрипт для создания начальных услуг:

```bash
# Создайте файл init_data.py на сервере
cat > init_data.py << 'EOF'
import requests

API = "http://localhost:8001/api"

# Логин
response = requests.post(f"{API}/admin/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()['token']
headers = {"Authorization": f"Bearer {token}"}

# Услуги
services = [
    {
        "name": "Классический маникюр",
        "description": "Профессиональный маникюр с покрытием гель-лаком.",
        "duration_minutes": 90,
        "price": 1500,
        "image_url": "https://images.pexels.com/photos/5128123/pexels-photo-5128123.jpeg"
    },
    {
        "name": "Педикюр",
        "description": "Комплексный уход за ногами.",
        "duration_minutes": 120,
        "price": 2000,
        "image_url": "https://images.unsplash.com/photo-1727199433272-70fdb94c8430"
    },
    {
        "name": "Маникюр + Педикюр",
        "description": "Комплексная программа ухода.",
        "duration_minutes": 180,
        "price": 3200,
        "image_url": "https://images.unsplash.com/photo-1666117584374-28eb6796f5d7"
    }
]

for service in services:
    requests.post(f"{API}/services", json=service, headers=headers)
    print(f"Created: {service['name']}")

# Расписание
for day in range(7):
    schedule = {
        "day_of_week": day,
        "start_time": "09:00",
        "end_time": "18:00",
        "is_working": day < 6
    }
    requests.post(f"{API}/schedule", json=schedule, headers=headers)
    print(f"Created schedule for day {day}")
EOF

# Запуск
pip3 install requests
python3 init_data.py
```

## 5. Доступ к приложению

- **Frontend**: http://your-server-ip:3000
- **Backend API**: http://your-server-ip:8001
- **API Docs**: http://your-server-ip:8001/docs
- **Админ-панель**: http://your-server-ip:3000/admin/login
  - Логин: admin
  - Пароль: (из .env файла)

## 6. Настройка Nginx (Production)

Для production рекомендуется использовать Nginx как reverse proxy:

```bash
# Установка Nginx
sudo apt install -y nginx

# Создание конфигурации
sudo nano /etc/nginx/sites-available/nail-salon
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/nail-salon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. SSL сертификат (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автообновление сертификата
sudo certbot renew --dry-run
```

## 8. Управление приложением

```bash
# Остановка
docker compose down

# Остановка с удалением volumes (все данные будут удалены!)
docker compose down -v

# Перезапуск
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart backend

# Просмотр логов
docker compose logs -f --tail=100

# Обновление после изменений кода
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 9. Резервное копирование MongoDB

```bash
# Создание бэкапа
docker compose exec mongodb mongodump --out /data/backup

# Копирование бэкапа на хост
docker cp nail-salon-mongodb:/data/backup ./mongodb-backup-$(date +%Y%m%d)

# Восстановление из бэкапа
docker compose exec mongodb mongorestore /data/backup
```

## 10. Автозапуск при перезагрузке сервера

Docker Compose с параметром `restart: unless-stopped` автоматически перезапустит контейнеры после перезагрузки сервера.

## 11. Мониторинг

```bash
# Использование ресурсов
docker stats

# Проверка здоровья контейнеров
docker compose ps

# Проверка логов на ошибки
docker compose logs | grep -i error
```

## Troubleshooting

### Проблемы с подключением к MongoDB

```bash
# Проверка логов MongoDB
docker compose logs mongodb

# Вход в контейнер MongoDB
docker compose exec mongodb mongosh
```

### Проблемы с backend

```bash
# Проверка логов
docker compose logs backend

# Вход в контейнер
docker compose exec backend bash

# Проверка переменных окружения
docker compose exec backend env
```

### Проблемы с frontend

```bash
# Пересборка с новыми переменными окружения
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Безопасность

1. **Измените все пароли по умолчанию** в .env файле
2. **Используйте сильный JWT_SECRET** (минимум 32 символа)
3. **Настройте firewall**:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **Регулярно обновляйте образы**:
   ```bash
   docker compose pull
   docker compose up -d
   ```
5. **Настройте CORS** правильно в production
6. **Используйте SSL сертификат** для HTTPS

## Дополнительные рекомендации

- Настройте регулярное резервное копирование MongoDB
- Используйте Docker volumes для постоянного хранения данных
- Настройте мониторинг (Prometheus + Grafana)
- Используйте Docker secrets для чувствительных данных в production
- Настройте log rotation для предотвращения переполнения диска

## Контакты и поддержка

При возникновении проблем проверьте логи всех сервисов:
```bash
docker compose logs
```