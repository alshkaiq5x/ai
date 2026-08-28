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


# =====================================================================
# 1. الأداة الرئيسية: TikTok Universal Patcher (من 360p إلى 4K 120fps)
# =====================================================================
# =====================================================================
# 1. TikTok Universal Patcher (مستقر 100% وبدون انهيار السيرفر)
# =====================================================================
@app.post("/tiktok-patcher", tags=["TikTok Optimizer"], summary="1. TikTok Universal Patcher (جميع الجودات - مستقر)")
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

    # 1. فحص الدقة بأمان
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        input_path
    ]

    maxrate = "5M"
    bufsize = "10M"
    level_val = "4.2"
    crf_val = "20"

    try:
        probe_res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        probe_data = json.loads(probe_res.stdout)
        video_stream = next((s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video'), {})

        height = int(video_stream.get('height', 1080))
        width = int(video_stream.get('width', 1920))
        max_dim = max(height, width)

        if max_dim >= 2160:
            maxrate = "18M"
            bufsize = "36M"
            level_val = "5.2"
            crf_val = "18"
        elif max_dim >= 1440:
            maxrate = "10M"
            bufsize = "20M"
            level_val = "5.1"
            crf_val = "19"
        elif max_dim >= 1080:
            maxrate = "5.5M"
            bufsize = "11M"
            level_val = "4.2"
            crf_val = "20"
        else:
            maxrate = "2.5M"
            bufsize = "5M"
            level_val = "3.2"
            crf_val = "22"
    except Exception:
        pass

    # 2. أمر FFmpeg المستقر بدون Deadlock
    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",            # حل مشكلة time=N/A وتزامن البداية
        "-threads", "1",                 # خيط واحد لتفادي استهلاك الذاكرة المفاجئ
        "-i", input_path,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-level:v", level_val,
        "-crf", crf_val,
        "-maxrate", maxrate,
        "-bufsize", bufsize,
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-color_range", "tv",
        "-c:a", "copy",                  # نسخ الصوت الأصلي لمنع تجميد Lavc AAC
        "-brand", "mp41",
        "-metadata", "title=ALSHKA IQ MAX QUALITY + FPS",
        "-metadata", "artist=ALSHKA IQ",
        "-metadata", "comment=Patched by ALSHKA IQ",
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
