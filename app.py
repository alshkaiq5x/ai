import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Blur Motion Smooth 60FPS Video Enhancer")

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

@app.post("/enhance")
async def enhance_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    target_height: int = 1080,
    blur_amount: int = 3  # قوة سلاسة الـ Blur (اختر من 2 إلى 5)
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_out.mp4")

    # حفظ الفيديو المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. scale: تحسين الأبعاد والدقة عبر Lanczos
    # 2. unsharp: الحفاظ على وضوح التفاصيل الثابتة
    # 3. tmix: خوارزمية Motion Blur التراكمي (نفس تأثير تطبيق Blur)
    # 4. framerate: توليد الحركة السلسة 60fps
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
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت المعالجة أثناء تطبيق Motion Blur")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"BlurSmooth_60fps_{file.filename}"
    )
