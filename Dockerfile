FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set non-interactive to avoid timezone prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for OpenCV and Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Symlink python3 to python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Create working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn gunicorn pydantic-settings

# Copy the entire app
COPY . .

# Expose the API port
EXPOSE 8000

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Run the app
CMD ["python", "main.py"]
