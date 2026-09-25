# Handoff frontend: Vue built into static files, served by nginx.
# Build from the repo root:
#   docker build -t handoff-frontend ./frontend

# Stage 1: build the static files with Node.
FROM node:22-slim AS builder

WORKDIR /app

# Dependencies first, for the same layer caching as the backend.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The browser calls this address, so it is baked in at build time.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: serve only the built files. This nginx image runs as a
# non-root user and listens on port 8080.
FROM nginxinc/nginx-unprivileged:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080