# Stage 1: Build the React Frontend
FROM node:20-bookworm AS frontend_builder

WORKDIR /app/apps/graphdash_new

# Copy package files
COPY apps/graphdash_new/package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY apps/graphdash_new/ ./

# Build the app (Vite)
RUN npm run build


# Stage 2: Python Backend Runtime
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (gcc might be needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code (respecting .dockerignore)
COPY . .

# Copy built frontend assets from Stage 1 to the correct location for FastAPI mount
# Default location in server.py is "apps/graphdash_new/dist" relative to project root
COPY --from=frontend_builder /app/apps/graphdash_new/dist /app/apps/graphdash_new/dist

# Expose port (FastAPI default)
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "-m", "uvicorn", "nmie.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
