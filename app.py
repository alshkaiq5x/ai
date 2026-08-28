import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Video Enhancer Suite")

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

# ==========================================
# 1. تحسين الدقة العالية (HD + 60FPS)
# ==========================================
@app.post("/enhance-hd", summary="1. رفع الدقة الحقيقية (Lanczos HD) + 60FPS")
async def enhance_hd(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    target_height: int = 1080
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_hd.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت معالجة الـ HD")

    background_tasks.add_task(cleanup_files, input_path, output_path)
    return FileResponse(path=output_path, media_type="video/mp4", filename=f"HD_{file.filename}")


# ==========================================
# 2. سلاسة موشن بلور (Blur App Effect)
# ==========================================
@app.post("/enhance-blur", summary="2. سلاسة حركية سينمائية (Motion Blur + 60FPS)")
async def enhance_blur(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    target_height: int = 1080,
    blur_amount: int = 3
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_blur.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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
    except subprocess.CalledProcessError:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت معالجة الـ Motion Blur")

    background_tasks.add_task(cleanup_files, input_path, output_path)
    return FileResponse(path=output_path, media_type="video/mp4", filename=f"BlurSmooth_{file.filename}")# ==========================================
# 3. تيك توك: فقط Pad / Patch لأبعاد 9:16
# ==========================================
@app.post("/tiktok-pad-only", summary="3. تيك توك: فقط إضافة هوامش (Pad 9:16) بدون أي تعديل آخر")
async def tiktok_pad_only(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{task_id}_in.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{task_id}_tiktok_pad.mp4")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # وضع الفيديو كاملاً في المنتصف وإضافة هوامش سوداء لملء 1080x1920 فقط
    vf_filter = (
        "scale='min(1080,iw*1920/ih)':'min(1920,ih*1080/iw)':force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(1080-iw)/2:(1920-ih)/2:color=black,"
        "setsar=1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        cleanup_files(input_path, output_path)
        raise HTTPException(status_code=500, detail="فشلت إضافة الـ Pad للفيديو")

    background_tasks.add_task(cleanup_files, input_path, output_path)
    return FileResponse(path=output_path, media_type="video/mp4", filename=f"TikTok_Pad_{file.filename}")
