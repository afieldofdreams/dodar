# syntax=docker/dockerfile:1.7

FROM node:22-alpine AS build
WORKDIR /app/site
COPY site/package.json site/package-lock.json ./
RUN npm ci
COPY site/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/site/dist /usr/share/nginx/html
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;
  location / {
    try_files $uri $uri/ /index.html;
  }
}
EOF
EXPOSE 80
