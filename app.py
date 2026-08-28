import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Video Enhancer & TikTok Optimizer")

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

# --- الخيار الأول: تحسين عام وسلاسة Blur 60FPS ---
@app.post("/enhance", summary="تحسين عام وسلاسة Blur 60FPS")
async def enhance_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    target_height: int = 1080,
    blur_amount: int = 3
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_out.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    weights = " ".join(["1"] * blur_amount)
    vf_filter = (
        f"scale=-2:{target_height}:flags=lanczos,"
        f"unsharp=5:5:0.7:5:5:0.0,"
        f"tmix=frames={blur_amount}:weights='{weights}',"
        f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت عملية التحسين")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"Enhanced_{file.filename}"
    )

# --- الخيار الثاني: TikTok Optimizer (9:16 + 60FPS + Blur + حماية جودة الرفع) ---
@app.post("/tiktok-optimizer", summary="أداة تجهيز الفيديو للتيك توك بأعلى جودة وسلاسة")
async def tiktok_optimizer(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    blur_amount: int = 3,
    fit_mode: str = "crop" # "crop" لملء الشاشة بالكامل 9:16 أو "pad" لوضع حواف سوداء/خلفية
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_tiktok.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    weights = " ".join(["1"] * blur_amount)

    # ضبط أبعاد 1080x1920 الخاصة بالتيك توك
    if fit_mode == "crop":
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    else:
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"

    vf_filter = (
        f"{scale_filter},"
        f"unsharp=5:5:0.8:5:5:0.0,"
        f"tmix=frames={blur_amount}:weights='{weights}',"
        f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-profile:v", "high","-level", "4.2",
        "-preset", "fast",
        "-crf", "18",
        "-maxrate", "12M",
        "-bufsize", "24M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart", # تسريع تشغيل الفيديو على التيك توك مباشرة
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت معالجة فيديو TikTok")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"TikTok_Ready_60fps_{file.filename}"
    )
