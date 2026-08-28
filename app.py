import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Real HD 60FPS Video Enhancer")

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
    target_height: int = 1080  # 1080 لـ Full HD أو 2160 لـ 4K
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_out.mp4")

    # حفظ الفيديو المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # سلسلة فلاتر معالجة الجودة الفائقة:
    # 1. scale lanczos: رفع الدقة بدقة متناهية
    # 2. unsharp: زيادة حدة التفاصيل وإزالة التغبيش
    # 3. framerate interpolation: توليد إطارات متداخلة حقيقية وسلسة
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
        "-preset", "medium",     # توازن ممتاز بين سرعة المعالجة ونقاء الصورة
        "-crf", "17",            # جودة بصرية فائقة الوضوح (Visually Lossless)
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت المعالجة أثناء تحسين الجودة")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"HD_{target_height}p_60fps_{file.filename}"
    )
