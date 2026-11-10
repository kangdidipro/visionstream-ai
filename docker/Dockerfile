FROM python:3.11-slim

# Prevent interactive prompts and Python bytecode/buffering issues
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    YOLO_CONFIG_DIR=/app/data/models \
    TORCH_HOME=/app/data/models

# Install system dependencies including FFmpeg, libGL, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install CPU-only PyTorch first for fast caching
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

# Create standard directories
RUN mkdir -p /app/src /app/data/inputs /app/data/outputs /app/data/models /app/logs /app/reports

CMD ["python3", "-c", "print('VisionStream AI Docker Container Ready.')"]
