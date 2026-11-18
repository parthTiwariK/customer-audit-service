FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV RUN_MIGRATIONS=0
COPY pyproject.toml requirements.txt README.md ./
COPY backend ./backend
COPY data ./data
COPY deploy ./deploy
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh
RUN chmod +x ./scripts/entrypoint.sh \
    && pip install --no-cache-dir -e .
COPY --from=frontend-build /build/dist ./frontend/dist
EXPOSE 8000
CMD ["/app/scripts/entrypoint.sh"]