# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory in container
WORKDIR /app

# Copy requirements.txt (if you have one)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Make port available to the world outside the container
ENV PORT 8080

# Set environment variables for Gunicorn
ENV PYTHONUNBUFFERED True

# Run Gunicorn with your specified configuration
CMD exec gunicorn --workers=1 --threads=2 --keep-alive 0 --bind :$PORT app:app
