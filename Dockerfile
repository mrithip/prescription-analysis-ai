FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    build-essential \
    cmake \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Create models directory explicitly to ensure it exists
RUN mkdir -p /app/models

# Copy the models folder (satisfied by the GitHub Action creating a dummy)
COPY ./models /app/models

# Copy the rest of your code
COPY . .

EXPOSE 5000

# Set environment variables for the container
ENV FLASK_APP=main.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]