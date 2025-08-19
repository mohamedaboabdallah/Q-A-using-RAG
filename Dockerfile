FROM node:18-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
ENV PUBLIC_URL=/
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL
COPY frontend/ ./
RUN npm run build

# ===== Stage 2: Python runtime =====
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080
WORKDIR /app

# persist caches & data across restarts/redeploys
ENV XDG_CACHE_HOME=/root/.cache
VOLUME ["/root/.cache/chroma", "/app/database"]
RUN mkdir -p /app/database

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/chroma_store ./chroma_store
COPY backend/text_extraction ./text_extraction
COPY backend/user_auth ./user_auth
COPY backend/llms ./llms
COPY backend/server.py ./server.py

COPY --from=frontend /frontend/build /app/frontend/build

EXPOSE 8080
CMD ["gunicorn","-w","1","-k","gthread","-t","120","-b","0.0.0.0:8080","server:app"]
