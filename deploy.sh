#!/bin/bash

# Скрипт для развертывания приложения Nail Salon

set -e

echo "🚀 Начинаем развертывание Nail Salon Booking System..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен. Установите Docker и попробуйте снова.${NC}"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker и Docker Compose установлены${NC}"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env файл не найден. Создаю из .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  ВАЖНО: Отредактируйте .env файл и установите безопасные пароли!${NC}"
        echo -e "${YELLOW}   Затем запустите скрипт снова.${NC}"
        exit 0
    else
        echo -e "${RED}❌ .env.example не найден${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ .env файл найден${NC}"

# Остановка старых контейнеров если они запущены
echo "🛑 Остановка старых контейнеров..."
docker compose down 2>/dev/null || true

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker compose build --no-cache

# Запуск контейнеров
echo "▶️  Запуск контейнеров..."
docker compose up -d

# Ожидание запуска всех сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
echo "📊 Проверка статуса контейнеров..."
docker compose ps

# Проверка здоровья backend
echo "🏥 Проверка здоровья backend API..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8001/api/ &> /dev/null; then
        echo -e "${GREEN}✅ Backend API работает${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "Попытка $attempt из $max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Backend API не запустился. Проверьте логи: docker compose logs backend${NC}"
    exit 1
fi

# Проверка здоровья frontend
echo "🏥 Проверка здоровья frontend..."
if curl -f http://localhost:3000 &> /dev/null; then
    echo -e "${GREEN}✅ Frontend работает${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend еще запускается. Может потребоваться немного времени.${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Развертывание завершено успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "🌐 Доступ к приложению:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "👤 Админ-панель: http://localhost:3000/admin/login"
echo "   Логин: admin"
echo "   Пароль: (из .env файла)"
echo ""
echo "📝 Полезные команды:"
echo "   Просмотр логов: docker compose logs -f"
echo "   Остановка: docker compose down"
echo "   Перезапуск: docker compose restart"
echo ""
echo "📚 Для инициализации данных выполните:"
echo "   python3 init_data.py"
echo ""
