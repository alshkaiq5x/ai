import os
import subprocess
import uuid
import shutil
from enum import Enum
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="AI Multi-Resolution, Multi-FPS & Motion Blur Enhancer")

UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ResolutionEnum(str, Enum):
    res_720p  = "720p (HD)"
    res_1080p = "1080p (Full HD)"
    res_2k    = "1440p (2K Quad HD)"
    res_4k    = "2160p (4K Ultra HD)"

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

@app.post("/enhance", summary="رفع الدقة حتى 4K + فريمات حتى 120fps + دعم Motion Blur")
async def enhance_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    resolution: ResolutionEnum = ResolutionEnum.res_1080p,
    fps: FPSEnum = FPSEnum.fps_60,
    enable_blur: bool = True,
    blur_amount: int = 3
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

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

    # الترتيب الأمثل لمنع انهيار الذاكرة:
    # 1. تطبيق Blur على الحجم الأصلي
    # 2. توليد الفريمات على الحجم الأصلي (خفيف جداً على الـ RAM)
    # 3. رفع الأبعاد إلى 4K كآخر خطوة
    filters = []

    if enable_blur and blur_amount > 1:
        weights = " ".join(["1"] * blur_amount)
        filters.append(f"tmix=frames={blur_amount}:weights='{weights}'")

    filters.append(f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100")
    filters.append(f"scale=-2:{target_height}:flags=bilinear")
    filters.append("unsharp=5:5:0.6:5:5:0.0")

    vf_filter = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",           # تقييد الخيوط لتجنب استهلاك RAM مفرط في 4K
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")
        last_lines = "\n".join(err.strip().splitlines()[-5:])
        raise HTTPException(status_code=500, detail=f"خطأ المعالجة: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"Enhanced_{target_height}p_{target_fps}fps_{file.filename}"
    )
