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
import os
import json
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

# =====================================================================
# TikTok Ultra Patcher (1080p60fps up to 4K 120fps) - ALSHKA IQ
# =====================================================================
@app.post("/tiktok-patcher", tags=["TikTok Optimizer"], summary="TikTok Patcher (1080p60fps -> 4K 120fps Ready)")
async def tiktok_patcher(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_opt.mp4")

    # حفظ الفيديو المرفوع
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. استخراج معلومات الفيديو لتحديد الدقة والفريمات
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        input_path
    ]
    
    maxrate = "8M"
    bufsize = "16M"
    try:
        probe_res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        probe_data = json.loads(probe_res.stdout)
        video_stream = next((s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video'), {})
        
        height = int(video_stream.get('height', 1080))
        width = int(video_stream.get('width', 1920))
        
        # ضبط البتريت بناءً على الدقة العالية (2K أو 4K)
        if height >= 2160 or width >= 2160:      # 4K UHD
            maxrate = "20M"
            bufsize = "40M"
        elif height >= 1440 or width >= 1440:    # 2K QHD
            maxrate = "12M"
            bufsize = "24M"
        else:                                    # 1080p 60fps
            maxrate = "7.5M"
            bufsize = "15M"
    except Exception:
        pass

    # 2. أمر FFmpeg المتقدم للدقات العالية والفريمات الفائقة
    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-i", input_path,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-level:v", "5.2",                       # المستوى القياسي لدعم 1080p60/120 و 4K
        "-crf", "18",                            # جودة نقية جداً
        "-maxrate", maxrate,
        "-bufsize", bufsize,
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-brand", "mp41",
        # حقوق ALSHKA IQ الرسمية
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
        filename=f"ALSHKA_IQ_Patched_{file.filename}"
    )
    # =====================================================================
# 2. ميزة رفع الفريمات فقط (Smooth Motion FPS)
# =====================================================================
@app.post("/fps-only", tags=["Performance"], summary="رفع الفريمات بسلاسة واستقرار تام")
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

    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",            # إعادة توليد التوقيت الزمني للإطارات لمنع التعليق
        "-threads", "1",                 # خيط واحد لتفادي نفاد ذاكرة السيرفر فوراً
        "-i", input_path,
        "-filter:v", f"fps={target_fps}",
        "-map", "0:v:0",
        "-map", "0:a?",                  # أخذ الصوت إن وُجد
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-maxrate", "5M",
        "-bufsize", "10M",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",                  # نسخ الصوت كما هو لتفادي خطأ معالج الصوت
        "-movflags", "+faststart",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files(input_path, output_path)
        err = e.stderr.decode("utf-8", errors="ignore")
        last_lines = "\n".join(err.strip().splitlines()[-5:])
        raise HTTPException(status_code=500, detail=f"فشلت معالجة الفريمات: {last_lines}")

    background_tasks.add_task(cleanup_files, input_path, output_path)

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"Smooth_{target_fps}fps_{file.filename}"
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
