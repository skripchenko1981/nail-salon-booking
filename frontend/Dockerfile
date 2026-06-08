# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Копіювання package files
COPY frontend/package.json frontend/yarn.lock ./

# Встановлення залежностей
RUN yarn install --frozen-lockfile

# Копіювання вихідного коду
COPY frontend/ .

# Build аргумент для backend URL
ARG REACT_APP_BACKEND_URL=https://nail-studio.pp.ua
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Білд застосунку
RUN yarn build

# Production stage
FROM nginx:alpine

# Копіювання custom nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Копіювання зібраних файлів з build stage
COPY --from=build /app/build /usr/share/nginx/html

# Відкриття порту
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
