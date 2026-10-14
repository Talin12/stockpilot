# syntax=docker/dockerfile:1

# ---- stage 1: build the static bundle with Node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# ---- stage 2: serve it with an unprivileged Nginx (no Node, no sources) ----
FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime
LABEL org.opencontainers.image.title="stockpilot-frontend" \
      org.opencontainers.image.description="StockPilot React dashboard served by Nginx" \
      org.opencontainers.image.licenses="MIT"

# Apply Alpine security fixes published after the base image was built.
USER root
RUN apk upgrade --no-cache
USER 101

ENV BACKEND_URL=http://backend:8000
COPY --chown=101:101 nginx/security-headers.conf /etc/nginx/security-headers.conf
COPY --chown=101:101 nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --chown=101:101 --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
