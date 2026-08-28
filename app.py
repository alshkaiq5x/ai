import os
import subprocess
import uuid
import shutil
from enum import Enum
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(
    title="Ultimate Video Suite: TikTok Patcher, AI Upscaler & Smooth FPS",
    description="منصة شاملة لمعالجة الفيديو: تخطي ضغط تيك توك، رفع الفريمات بسلاسة، ورفع الدقة حتى 4K.",
    version="2.0.0"
)

UPLOAD_DIR = "/tmp/uploads"
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# خيارات الجودة
class ResolutionEnum(str, Enum):
    res_720p  = "720p (HD)"
    res_1080p = "1080p (Full HD)"
    res_2k    = "1440p (2K Quad HD)"
    res_4k    = "2160p (4K Ultra HD)"

# خيارات الفريمات
class FPSEnum(int, Enum):
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

# =====================================================================
# TikTok Optimized Patcher (تخطي ضغط تيك توك وحفظ الألوان 100% ونفس الحجم)
# =====================================================================
@app.post("/tiktok-patcher", tags=["TikTok Tools"], summary="TikTok Optimized Patcher")
async def tiktok_patcher(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_patched.mp4")

    # حفظ الفيديو المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # تطبيق الباتش بنمط Optimized الحقيقي:
    # 1. -c:v copy & -c:a copy: نسخ مباشر بدون إعادة ضغط (نفس الحجم، بدون بطء، معالجة في ثانية واحدة)
    # 2. h264_metadata: إجبار تيك توك على قراءة ألوان BT.709 TV Range لمنع بهتان الألوان
    # 3. +faststart: نقل Moov Atom للأول لبدء تشغيل الفيديو فوراً وتفادي التشفير العشوائي
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-map", "0",
        "-c:v", "copy",
        "-bsf:v", "h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        # مسار احتياطي للترميزات الأخرى (مثل HEVC) لنقل الترويسة بنجاح
        fallback_cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0",
            "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]
        try:
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            cleanup_files(input_path, output_path)
            err = e.stderr.decode("utf-8", errors="ignore")
            last_lines = "\n".join(err.strip().splitlines()[-4:])
            raise HTTPException(status_code=500, detail=f"فشلت المعالجة: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"TikTok_Optimized_{file.filename}"
    )
    # =====================================================================
# 2. ميزة رفع الفريمات فقط (Smooth Motion FPS)
# =====================================================================
@app.post("/fps-only", tags=["Performance"], summary="رفع الفريمات مع إظهار البتريت والحجم على تيك توك")
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

    # حفظ الفيديو
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. فلتر الفريمات مع ضبط التوقيت الزمني الصارم (CFR)
    vf_filter = f"fps=fps={target_fps}:round=near,setpts=N/({target_fps}*TB)"

    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-i", input_path,
        "-vf", vf_filter,
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        # تحديد سقف البتريت والـ Buffer ليتم كتابتها رسميًا في ترويسة الفيديو
        "-maxrate", "14M",
        "-bufsize", "28M",
        # تثبيت الـ GOP (Keyframe كل 1 ثانية) ليتعرف تيك توك على معدل البت
        "-g", str(target_fps),
        "-keyint_min", str(target_fps),
        "-sc_threshold", "0",
        "-fps_mode", "cfr",             # إجبار التوقيت الثابت (Constant Frame Rate)
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",       # نقل الترويسة للبداية لقراءة فورية للحجم والبتريت
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
        filename=f"Smooth_{target_fps}fps_TikTokReady_{file.filename}"
    )

# =====================================================================
# 3. ميزة رفع الجودة والدقة فقط (Upscale Up to 4K)
# =====================================================================
@app.post("/upscale-only", tags=["Performance"], summary="3. رفع الجودة والدقة حتى 4K (بدون تغيير الفريمات)")
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
    else:
        scale_filter = f"scale=-2:{target_height}:flags=lanczos,unsharp=5:5:0.6:5:5:0.0"
        preset_val = "fast"
        thread_val = "2"

    cmd = [
        "ffmpeg", "-y",
        "-threads", thread_val,
        "-i", input_path,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-preset", preset_val,
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
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
        filename=f"HD_{target_height}p_{file.filename}"
    )

# =====================================================================
# 4. الميزة الشاملة (رفع الدقة + رفع الفريمات معاً)
# =====================================================================
@app.post("/all-in-one-combo", tags=["Combo Tools"], summary="4. دمج شامل: رفع الدقة حتى 4K + رفع الفريمات مع حركة سلسة")
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
        vf_filter = f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100,scale=-2:{target_height}:flags=bicubic"
        preset_val = "ultrafast"
        thread_val = "1"
    else:
        vf_filter = f"framerate=fps={target_fps}:interp_start=0:interp_end=255:scene=100,scale=-2:{target_height}:flags=lanczos,unsharp=5:5:0.6:5:5:0.0"
        preset_val = "fast"
        thread_val = "2"

    cmd = [
        "ffmpeg", "-y",
        "-threads", thread_val,
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", preset_val,
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
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
