import os
import json
import subprocess
import uuid
import shutil
from enum import Enum
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(
    title="ALSHKA IQ - Universal Video Processing & TikTok Optimizer",
    description="محرك معالجة فيديو متكامل يدعم جميع الجودات من 360p إلى 4K 120fps مع تخطي ضغط تيك توك والحفاظ على الألوان والحجم.",
    version="6.0.0"
)

# مسارات التخزين المؤقت
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
    fps_60  = 60
    fps_90  = 90
    fps_120 = 120

def cleanup_files(*paths):
    """تنظيف الملفات المؤقتة بعد انتهاء التحميل."""
    for p in paths:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

@app.post("/tiktok-patcher", tags=["TikTok Optimizer"], summary="TikTok Strict Optimized Patcher (Stable)")
async def tiktok_patcher(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_opt.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-threads", "1",
        "-i", input_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=60,setsar=1",
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-level:v", "4.2",
        "-crf", "19",
        "-maxrate", "4500k",
        "-bufsize", "9000k",
        "-g", "60",
        "-keyint_min", "60",
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-color_range", "tv",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-metadata", "title=ALSHKA IQ MAX QUALITY + FPS",
        "-metadata", "artist=ALSHKA IQ",
        "-metadata", "comment=Patched by ALSHKA IQ",
        "-metadata:s:v:0", "handler_name=ALSHKA Video Engine",
        "-metadata:s:a:0", "handler_name=ALSHKA Audio Engine",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")
        last_lines = "\n".join(err.strip().splitlines()[-4:])
        raise HTTPException(status_code=500, detail=f"فشلت المعالجة: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"ALSHKA_IQ_Optimized_{file.filename}"
    )
# =====================================================================
# 2. ميزة رفع الفريمات فقط (Smooth High FPS)
# =====================================================================
@app.post("/fps-only", tags=["Enhancement Tools"], summary="2. رفع الفريمات بحركة ناعمة ومستقرة (60 / 90 / 120 FPS)")
async def increase_fps_only(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    fps: FPSEnum = FPSEnum.fps_60
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    target_fps = int(fps.value)
    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_fps.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-threads", "1",
        "-i", input_path,
        "-filter:v", f"fps={target_fps}",
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "21",
        "-maxrate", "6M",
        "-bufsize", "12M",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")
        last_lines = "\n".join(err.strip().splitlines()[-4:])
        raise HTTPException(status_code=500, detail=f"فشلت معالجة الفريمات: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"Smooth_{target_fps}fps_{file.filename}"
    )


# =====================================================================
# 3. ميزة رفع الجودة والدقة فقط (Upscale up to 4K)
# =====================================================================
@app.post("/upscale-only", tags=["Enhancement Tools"], summary="3. رفع الجودة والدقة حتى 4K (بدون تغيير الفريمات)")
async def upscale_resolution_only(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    resolution: ResolutionEnum = ResolutionEnum.res_1080p
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

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_upscaled.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if target_height >= 2160:
        scale_filter = f"scale=-2:{target_height}:flags=bicubic"
        preset_val = "ultrafast"
        thread_val = "1"
        maxrate_val = "25M"
    else:
        scale_filter = f"scale=-2:{target_height}:flags=lanczos,unsharp=3:3:0.5:3:3:0.0"
        preset_val = "veryfast"
        thread_val = "2"
        maxrate_val = "16M"

    cmd = [
        "ffmpeg", "-y",
        "-threads", thread_val,
        "-i", input_path,
        "-vf", scale_filter,
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", preset_val,
        "-crf", "18",
        "-maxrate", maxrate_val,
        "-bufsize", "30M",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")
        last_lines = "\n".join(err.strip().splitlines()[-4:])
        raise HTTPException(status_code=500, detail=f"فشلت معالجة الجودة: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"HD_{target_height}p_{file.filename}"
    )


# =====================================================================
# 4. المعالجة المزدوجة الشاملة (رفع الدقة + الفريمات معاً)
# =====================================================================
@app.post("/all-in-one-combo", tags=["Combo Tools"], summary="4. دمج شامل: رفع الدقة حتى 4K + رفع الفريمات بسلاسة")
async def combo_enhance(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    resolution: ResolutionEnum = ResolutionEnum.res_1080p,
    fps: FPSEnum = FPSEnum.fps_60
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
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_combo.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if target_height >= 2160:
        vf_filter = f"fps={target_fps},scale=-2:{target_height}:flags=bicubic"
        preset_val = "ultrafast"
        thread_val = "1"
        maxrate_val = "25M"
    else:
        vf_filter = f"fps={target_fps},scale=-2:{target_height}:flags=lanczos,unsharp=3:3:0.5:3:3:0.0"
        preset_val = "veryfast"
        thread_val = "2"
        maxrate_val = "16M"

    cmd = [
        "ffmpeg", "-y",
        "-threads", thread_val,
        "-i", input_path,
        "-vf", vf_filter,
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", preset_val,
        "-crf", "18",
        "-maxrate", maxrate_val,
        "-bufsize", "30M",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")
        last_lines = "\n".join(err.strip().splitlines()[-4:])
        raise HTTPException(status_code=500, detail=f"فشلت المعالجة: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"Combo_{target_height}p_{target_fps}fps_{file.filename}"
    )
