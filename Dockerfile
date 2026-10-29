# Elder Monitor - container image (CPU only, headless)
FROM python:3.12-slim

# System libraries required by OpenCV
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

WORKDIR /app

# CPU-only PyTorch first (keeps the image several GB smaller than the CUDA build)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the pose model at build time so the container starts offline
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n-pose.pt')"

# Application code
COPY elder_monitor/ elder_monitor/
COPY main.py .

# Run as non-root user; /app/data holds zones.json (mounted volume)
RUN useradd --create-home monitor && mkdir -p /app/data && chown -R monitor /app
USER monitor

ENTRYPOINT ["python", "main.py", "--zones", "/app/data/zones.json"]
