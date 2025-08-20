# ===== Stage 1: Build React frontend =====
FROM node:18-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
ENV PUBLIC_URL=/
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL
COPY frontend/ ./
RUN npm run build

# ===== Stage 2: Python runtime =====
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080 XDG_CACHE_HOME=/root/.cache
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/* && update-ca-certificates
# Create cache + db dirs (Railway: mount volumes in UI, not via VOLUME keyword)
RUN mkdir -p /root/.cache/chroma /app/backend/database

# Install backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend ./backend

# Copy built frontend
COPY --from=frontend /app/frontend/build /app/frontend/build

# Let server.py know where frontend lives
ENV FRONTEND_BUILD_DIR=/app/frontend/build

EXPOSE 8080
CMD ["gunicorn","-w","1","-k","gthread","-t","120","-b","0.0.0.0:8080","backend.server:app"]
