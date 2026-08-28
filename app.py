import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Fast 60FPS Video Enhancer")

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
    target_height: int = 720
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_out.mp4")

    # حفظ الفيديو
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # فلتر سريع جداً لرفع الفريمات إلى 60 بحركة ناعمة وتغيير الدقة بدون كسر موارد السيرفر
    vf_filter = f"scale=-2:{target_height},fps=fps={target_fps},tblend=all_mode=average"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت المعالجة أثناء تشغيل FFmpeg")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"60fps_{file.filename}"
    )
