import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Real HD & Smooth 60FPS Enhancer")

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

@app.post("/enhance", summary="رفع الجودة الحقيقية + 60FPS بحركة سلسة")
async def enhance_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    target_height: int = 1080
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_enhanced.mp4")

    # حفظ الملف المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. scale lanczos: رفع الدقة مع الحفاظ على النقاء
    # 2. unsharp: زيادة حدة التفاصيل وإبراز الحواف بدقة
    # 3. framerate: توليد إطارات 60fps متداخلة بسلاسة حركية سينمائية
    vf_filter = (
        f"scale=-2:{target_height}:flags=lanczos,"
        f"unsharp=5:5:0.8:5:5:0.0,"
        f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",            # نقاء بصري فائق بدون تشويش في البيكسلات
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",          # نقل الصوت الأصلي بدون أي ضغط
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")[:200]
        raise HTTPException(status_code=500, detail=f"فشلت المعالجة: {err}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"HD_60fps_{file.filename}"
    )
