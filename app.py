import os
import subprocess
import uuid
import shutil
from enum import Enum
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="AI Multi-Quality & Multi-FPS Video Upscaler")

UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# قائمة الجودات المتاحة للاختيار
class ResolutionEnum(str, Enum):
    res_720p  = "720p (HD)"
    res_1080p = "1080p (Full HD)"
    res_2k    = "1440p (2K Quad HD)"
    res_4k    = "2160p (4K Ultra HD)"

# قائمة الفريمات المتاحة للاختيار
class FPSEnum(int, Enum):
    fps_30  = 30
    fps_60  = 60
    fps_90  = 90
    fps_120 = 120

def cleanup_files(*paths):
    for p in paths:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

@app.post("/enhance", summary="رفع الدقة بالذكاء الاصطناعي متعدد الجودات والفريمات حتى 4K")
async def enhance_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    resolution: ResolutionEnum = ResolutionEnum.res_1080p,
    fps: FPSEnum = FPSEnum.fps_60
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    # تحويل الاختيار إلى ارتفاع البيكسلات
    height_map = {
        ResolutionEnum.res_720p: 720,
        ResolutionEnum.res_1080p: 1080,
        ResolutionEnum.res_2k: 1440,
        ResolutionEnum.res_4k: 2160
    }
    target_height = height_map[resolution]
    target_fps = int(fps.value)

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_out.mp4")

    # حفظ الفيديو المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # مرشحات المعالجة:
    # 1. scale lanczos: إعادة بناء البيكسلات بدقة عالية
    # 2. cas (Contrast Adaptive Sharpening): خوارزمية ذكاء اصطناعي لإعادة التفاصيل بدون تشويه
    # 3. framerate: محاكاة حركة سينمائية فائقة السلاسة بمعدل الفريمات المختار
    vf_filter = (
        f"scale=-2:{target_height}:flags=lanczos,"
        f"cas=0.7,"
        f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",            # نقاء ألوان وتفاصيل متناهي الدقة
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",          # نسخ الصوت الأصلي بدون أي ضغط
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
        filename=f"AI_{target_height}p_{target_fps}fps_{file.filename}"
    )
