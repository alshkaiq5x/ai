import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="AI Video Upscaler (Real-ESRGAN) + 60FPS")

BASE_DIR = "/tmp/processing"
os.makedirs(BASE_DIR, exist_ok=True)

def cleanup_directory(path: str):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except Exception:
            pass

@app.post("/enhance-ai")
async def enhance_ai_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_fps: int = 60,
    model_name: str = "realesr-animevideov3",
    upscale_ratio: int = 2
):
    # التحقق من الامتداد
    if not file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="صيغة الفيديو غير مدعومة")

    task_id = str(uuid.uuid4())
    task_dir = os.path.join(BASE_DIR, task_id)
    frames_in = os.path.join(task_dir, "frames_in")
    frames_out = os.path.join(task_dir, "frames_out")
    
    os.makedirs(frames_in, exist_ok=True)
    os.makedirs(frames_out, exist_ok=True)

    input_video = os.path.join(task_dir, "input.mp4")
    output_video = os.path.join(task_dir, f"ai_enhanced_60fps_{file.filename}")

    # حفظ الفيديو المرفوع
    with open(input_video, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # قراءة معدل الإطارات الأصلي
        fps_probe = subprocess.run(
            ["ffprobe", "-v", "0", "-of", "csv=p=0", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", input_video],
            capture_output=True, text=True, check=True
        )
        original_fps = fps_probe.stdout.strip()

        # تفكيك الفيديو إلى إطارات
        subprocess.run([
            "ffmpeg", "-y", "-i", input_video,
            "-qscale:v", "2",
            os.path.join(frames_in, "frame_%08d.png")
        ], check=True)

        # رفع الدقة بالذكاء الاصطناعي
        subprocess.run([
            "realesrgan-ncnn-vulkan",
            "-i", frames_in,
            "-o", frames_out,
            "-n", model_name,
            "-s", str(upscale_ratio),
            "-f", "png"
        ], check=True)

        # رفع الفريمات إلى 60 عبر التدفق البصري ودمج الصوت
        vf_filter = f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
        
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", original_fps,
            "-i", os.path.join(frames_out, "frame_%08d.png"),
            "-i", input_video,
            "-vf", vf_filter,
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_video
        ], check=True)
    except subprocess.CalledProcessError as e:
        cleanup_directory(task_dir)
        raise HTTPException(status_code=500, detail=f"فشلت المعالجة: {e.stderr if hasattr(e, 'stderr') else str(e)}")

    # تنظيف المجلد المؤقت بعد انتهاء التحميل
    background_tasks.add_task(cleanup_directory, task_dir)

    return FileResponse(
        path=output_video,
        media_type="video/mp4",
        filename=f"ai_60fps_{file.filename}"
    )
