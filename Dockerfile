FROM python:3.11-slim

# تثبيت الأدوات المساعدة ومكتبات FFmpeg و Vulkan
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    unzip \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# تنزيل وإعداد أداة Real-ESRGAN NCNN
WORKDIR /opt/realesrgan
RUN wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip \
    && unzip realesrgan-ncnn-vulkan-20220424-ubuntu.zip \
    && rm realesrgan-ncnn-vulkan-20220424-ubuntu.zip \
    && chmod +x realesrgan-ncnn-vulkan \
    && ln -s /opt/realesrgan/realesrgan-ncnn-vulkan /usr/local/bin/realesrgan-ncnn-vulkan

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
