import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="TikTok 9:16 Pad & 60FPS Enhancer")

UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def cleanup_files(*paths):
    for p in paths:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

@app.post("/tiktok-pad", summary="تجهيز الفيديو للتيك توك 9:16 بنظام Pad مع 60FPS")
async def tiktok_pad(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_tiktok.mp4")

    # حفظ الفيديو المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. ضبط أبعاد الفيديو ليناسب 1080x1920 مع إضافة Pad (حواف) بشكل آمن وضمان أرقام زوجية
    # 2. unsharp لزيادة الحدة
    # 3. framerate لتوليد 60 إطاراً بنعومة بدون استهلاك زائد للذاكرة
    vf_filter = (
        "scale='min(1080,iw*1920/ih)':'min(1920,ih*1080/iw)':force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(1080-iw)/2:(1920-ih)/2:color=black,"
        "setsar=1,"
        "unsharp=5:5:0.7:5:5:0.0,"
        f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err_msg = e.stderr.decode("utf-8", errors="ignore")[:300]
        raise HTTPException(status_code=500, detail=f"خطأ FFmpeg: {err_msg}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"TikTok_Pad_60fps_{file.filename}"
    )
