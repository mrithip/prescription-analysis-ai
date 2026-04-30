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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- BAKING HAPPENS HERE ---
# Copy the models folder from your computer into the image
COPY ./models /app/models
# Copy the rest of your code
COPY . .

EXPOSE 5000
CMD ["python", "main.py"]