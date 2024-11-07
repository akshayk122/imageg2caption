# Use official Python runtime as base image
FROM python:3.12-slim

# Install system dependencies required for Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory in container
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Make port available to the world outside the container
ENV PORT 8080

# Set environment variables for Gunicorn and Python
ENV PYTHONUNBUFFERED True
ENV PYTHONPATH /app

# Create directory for Google Cloud credentials
RUN mkdir -p /root/.config/gcloud

# Run Gunicorn
CMD exec gunicorn --workers=1 --threads=1 --keep-alive 0 --timeout 0 --bind :$PORT app:app
