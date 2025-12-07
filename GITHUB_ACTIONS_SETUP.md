# Настройка GitHub Actions для автоматического развертывания

## Обзор

GitHub Actions workflow автоматически:
1. Собирает Docker образы при каждом push в `main` или `production` ветки
2. Публикует образы в GitHub Container Registry
3. Развертывает на production сервере (только для ветки `production`)

## Настройка GitHub Secrets

Перейдите в Settings → Secrets and variables → Actions и добавьте следующие секреты:

### Обязательные секреты для development (branch: main)

Эти секреты нужны только для сборки образов:

```
REACT_APP_BACKEND_URL
```
- URL вашего backend API
- Пример: `https://api.yourdomain.com`

### Дополнительные секреты для production (branch: production)

Для автоматического развертывания на сервер:

```
SERVER_HOST
```
- IP адрес или домен вашего сервера
- Пример: `123.45.67.89` или `server.yourdomain.com`

```
SERVER_USERNAME
```
- Имя пользователя SSH
- Пример: `ubuntu` или `root`

```
SERVER_SSH_KEY
```
- Приватный SSH ключ для доступа к серверу
- Как получить:
  ```bash
  # На вашем компьютере
  cat ~/.ssh/id_rsa
  # Скопируйте весь вывод, включая BEGIN и END строки
  ```

```
SERVER_PORT
```
- SSH порт (опционально, по умолчанию 22)
- Пример: `22`

## Настройка SSH доступа на сервере

### 1. Создание SSH ключа (если еще не создан)

На вашем локальном компьютере:
```bash
ssh-keygen -t rsa -b 4096 -C "github-actions@yourdomain.com"
```

### 2. Копирование публичного ключа на сервер

```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub username@server-ip
```

ИЛИ вручную:
```bash
# На сервере
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Вставьте содержимое вашего публичного ключа (id_rsa.pub)
chmod 600 ~/.ssh/authorized_keys
```

### 3. Проверка SSH доступа

```bash
ssh -i ~/.ssh/id_rsa username@server-ip
```

## Подготовка сервера

На production сервере выполните:

```bash
# Создайте директорию для приложения
sudo mkdir -p /opt/nail-salon-booking
sudo chown $USER:$USER /opt/nail-salon-booking
cd /opt/nail-salon-booking

# Клонируйте репозиторий
git clone https://github.com/your-username/nail-salon-booking.git .

# Создайте .env файл
cp .env.example .env
nano .env  # Настройте переменные окружения

# Создайте docker-compose.yml для production
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: nail-salon-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
    networks:
      - nail-salon-network

  backend:
    image: ghcr.io/your-username/nail-salon-booking/backend:latest
    container_name: nail-salon-backend
    restart: unless-stopped
    environment:
      MONGO_URL: mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@mongodb:27017/
      DB_NAME: ${DB_NAME}
      CORS_ORIGINS: ${CORS_ORIGINS}
      JWT_SECRET: ${JWT_SECRET}
      ADMIN_USERNAME: ${ADMIN_USERNAME}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
    networks:
      - nail-salon-network

  frontend:
    image: ghcr.io/your-username/nail-salon-booking/frontend:latest
    container_name: nail-salon-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - nail-salon-network

volumes:
  mongodb_data:

networks:
  nail-salon-network:
    driver: bridge
EOF
```

## Включение GitHub Container Registry

### 1. Создание Personal Access Token (PAT)

1. Перейдите в GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Нажмите "Generate new token (classic)"
3. Выберите scopes:
   - `write:packages` (автоматически включает `read:packages`)
   - `delete:packages` (опционально)
4. Скопируйте сгенерированный токен

### 2. Настройка доступа к GitHub Container Registry на сервере

На production сервере:
```bash
# Логин в GitHub Container Registry
echo "YOUR_PAT_TOKEN" | docker login ghcr.io -u your-github-username --password-stdin
```

## Workflow ветвей

### Development (branch: main)
- Каждый push в `main` → сборка и публикация образов с тегом `main-{sha}`
- Автоматическое развертывание не происходит

### Production (branch: production)
- Каждый push в `production` → сборка, публикация и автоматическое развертывание
- Образы помечаются как `latest`

## Запуск workflow

### Автоматический запуск
Workflow запускается автоматически при:
- Push в ветки `main` или `production`

### Ручной запуск
1. Перейдите в Actions → Deploy Nail Salon Booking System
2. Нажмите "Run workflow"
3. Выберите ветку
4. Нажмите "Run workflow"

## Мониторинг развертывания

### В GitHub
1. Перейдите в Actions
2. Выберите последний workflow run
3. Просмотрите логи каждого шага

### На сервере
```bash
# Просмотр статуса контейнеров
docker compose ps

# Просмотр логов
docker compose logs -f

# Проверка работоспособности
curl http://localhost:8001/api/
curl http://localhost:3000
```

## Откат к предыдущей версии

Если что-то пошло не так:

```bash
# На сервере
cd /opt/nail-salon-booking

# Просмотр доступных тегов
docker images | grep nail-salon

# Откат на конкретную версию
docker compose down
docker tag ghcr.io/your-username/nail-salon-booking/backend:main-abc123 ghcr.io/your-username/nail-salon-booking/backend:latest
docker tag ghcr.io/your-username/nail-salon-booking/frontend:main-abc123 ghcr.io/your-username/nail-salon-booking/frontend:latest
docker compose up -d
```

## Безопасность

1. ✅ Никогда не храните секреты в коде
2. ✅ Используйте GitHub Secrets для конфиденциальных данных
3. ✅ Ограничьте SSH доступ только для необходимых IP
4. ✅ Регулярно обновляйте SSH ключи
5. ✅ Используйте separate environments для dev/staging/production

## Troubleshooting

### Ошибка "Permission denied (publickey)"
- Проверьте, что правильный SSH ключ добавлен в GitHub Secrets
- Убедитесь, что публичный ключ добавлен в `~/.ssh/authorized_keys` на сервере

### Ошибка "Cannot connect to Docker daemon"
- Убедитесь, что Docker установлен и запущен на сервере
- Проверьте, что пользователь добавлен в группу docker: `sudo usermod -aG docker $USER`

### Образы не скачиваются
- Проверьте, что вы авторизованы в GitHub Container Registry на сервере
- Убедитесь, что пакет публичный или у вас есть токен доступа

### Сервис не запускается после развертывания
- Проверьте логи: `docker compose logs`
- Убедитесь, что .env файл на сервере настроен правильно
- Проверьте переменные окружения: `docker compose config`

## Дополнительные интеграции

### Уведомления в Slack

Добавьте в конец `.github/workflows/deploy.yml`:

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Deployment to production'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
  if: always()
```

### Уведомления в Telegram

Добавьте секреты `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`, затем:

```yaml
- name: Notify Telegram
  uses: appleboy/telegram-action@master
  with:
    to: ${{ secrets.TELEGRAM_CHAT_ID }}
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    message: |
      ✅ Deployment successful!
      Branch: ${{ github.ref }}
      Commit: ${{ github.sha }}
```

## Контакты

При возникновении проблем создайте Issue в GitHub репозитории.
