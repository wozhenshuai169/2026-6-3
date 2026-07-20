"""Build the latest real-operation competition demo video.

This script replaces selected picture regions in the existing seven-minute cut.
The original audio stream and the burned-in subtitle strip are preserved.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CACHE_SITE = Path.home() / ".cache" / "codex-video-tools"
if CACHE_SITE.exists():
    sys.path.insert(0, str(CACHE_SITE))

from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # noqa: E402
import imageio_ffmpeg  # noqa: E402


VIDEO_DIR = ROOT / "deliverables" / "competition-video"
CAPTURE_DIR = VIDEO_DIR / "latest-rerecord"
PROCESSED_DIR = CAPTURE_DIR / "processed"
CLIP_DIR = CAPTURE_DIR / "clips"
BASE_VIDEO = VIDEO_DIR / "云游智导_三端全功能_程序原声_黑栏字幕_7分钟.mp4"
OUTPUT_VIDEO = VIDEO_DIR / "云游智导_三端全功能_真实操作_最新音色形象_7分钟.mp4"

FRAME_RATE = 2
OUTPUT_RATE = 24
WIDTH = 1920
TOP_HEIGHT = 1014

SEGMENTS = (
    ("landing", "full", 20, 10),
    ("visitor-avatar", "phone", 150, 28),
    ("guide", "phone", 240, 60),
    ("admin-avatar", "full", 375, 20),
)


def warm_blurred_background(source: Image.Image) -> Image.Image:
    background = ImageOps.fit(
        source,
        (WIDTH, TOP_HEIGHT),
        method=Image.Resampling.LANCZOS,
    ).filter(ImageFilter.GaussianBlur(30))
    background = ImageEnhance.Brightness(background).enhance(0.46)
    tint = Image.new("RGB", background.size, (238, 225, 207))
    return Image.blend(background, tint, 0.34)


def render_full(source: Image.Image) -> Image.Image:
    canvas = warm_blurred_background(source)
    scale = min(WIDTH / source.width, TOP_HEIGHT / source.height)
    size = (round(source.width * scale), round(source.height * scale))
    foreground = source.resize(size, Image.Resampling.LANCZOS)
    x = (WIDTH - foreground.width) // 2
    y = (TOP_HEIGHT - foreground.height) // 2
    shadow = Image.new("RGBA", (foreground.width + 28, foreground.height + 28), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", shadow.size, (0, 0, 0, 70)).filter(ImageFilter.GaussianBlur(14))
    canvas.paste(shadow_layer, (x - 14, y - 6), shadow_layer)
    canvas.paste(foreground, (x, y))
    return canvas


def render_phone(source: Image.Image) -> Image.Image:
    canvas = warm_blurred_background(source)
    crop_width = min(450, source.width)
    left = max(0, (source.width - crop_width) // 2)
    phone = source.crop((left, 0, left + crop_width, source.height))
    scale = TOP_HEIGHT / phone.height
    phone = phone.resize((round(phone.width * scale), TOP_HEIGHT), Image.Resampling.LANCZOS)
    x = (WIDTH - phone.width) // 2
    shadow = Image.new("RGBA", (phone.width + 48, TOP_HEIGHT + 12), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", shadow.size, (0, 0, 0, 105)).filter(ImageFilter.GaussianBlur(20))
    canvas.paste(shadow_layer, (x - 24, -2), shadow_layer)
    canvas.paste(phone, (x, 0))
    return canvas


def prepare_frames(name: str, mode: str, duration: int) -> None:
    source_dir = CAPTURE_DIR / name
    target_dir = PROCESSED_DIR / name
    target_dir.mkdir(parents=True, exist_ok=True)
    frames = sorted(source_dir.glob("frame-*.png"))
    expected = duration * FRAME_RATE
    if len(frames) != expected:
        raise RuntimeError(f"{name}: expected {expected} frames, found {len(frames)}")

    for index, frame_path in enumerate(frames):
        with Image.open(frame_path) as loaded:
            source = loaded.convert("RGB")
        rendered = render_phone(source) if mode == "phone" else render_full(source)
        rendered.save(target_dir / f"frame-{index:04d}.jpg", quality=95, subsampling=0, optimize=True)


def run(command: list[str]) -> None:
    print(" ".join(command))
    subprocess.run(command, check=True)


def build_clips(ffmpeg: str) -> list[Path]:
    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    for name, mode, _start, duration in SEGMENTS:
        prepare_frames(name, mode, duration)
        clip = CLIP_DIR / f"{name}.mp4"
        run(
            [
                ffmpeg,
                "-y",
                "-framerate",
                str(FRAME_RATE),
                "-i",
                str(PROCESSED_DIR / name / "frame-%04d.jpg"),
                "-an",
                "-vf",
                f"fps={OUTPUT_RATE},format=yuv420p",
                "-t",
                str(duration),
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-movflags",
                "+faststart",
                str(clip),
            ]
        )
        clips.append(clip)
    return clips


def compose(ffmpeg: str, clips: list[Path]) -> None:
    inputs: list[str] = ["-i", str(BASE_VIDEO)]
    for clip in clips:
        inputs.extend(["-i", str(clip)])

    filter_graph = ";".join(
        [
            "[0:v]split=9[s0][s1][s2][s3][s4][s5][s6][s7][s8]",
            "[s0]trim=start=0:end=20,setpts=PTS-STARTPTS[v0]",
            "[s1]trim=start=20:end=30,setpts=PTS-STARTPTS[b1]",
            "[1:v]setpts=PTS-STARTPTS[o1]",
            "[b1][o1]overlay=0:0:shortest=1[v1]",
            "[s2]trim=start=30:end=150,setpts=PTS-STARTPTS[v2]",
            "[s3]trim=start=150:end=178,setpts=PTS-STARTPTS[b3]",
            "[2:v]setpts=PTS-STARTPTS[o3]",
            "[b3][o3]overlay=0:0:shortest=1[v3]",
            "[s4]trim=start=178:end=240,setpts=PTS-STARTPTS[v4]",
            "[s5]trim=start=240:end=300,setpts=PTS-STARTPTS[b5]",
            "[3:v]setpts=PTS-STARTPTS[o5]",
            "[b5][o5]overlay=0:0:shortest=1[v5]",
            "[s6]trim=start=300:end=375,setpts=PTS-STARTPTS[v6]",
            "[s7]trim=start=375:end=395,setpts=PTS-STARTPTS[b7]",
            "[4:v]setpts=PTS-STARTPTS[o7]",
            "[b7][o7]overlay=0:0:shortest=1[v7]",
            "[s8]trim=start=395,setpts=PTS-STARTPTS[v8]",
            "[v0][v1][v2][v3][v4][v5][v6][v7][v8]concat=n=9:v=1:a=0[outv]",
        ]
    )

    run(
        [
            ffmpeg,
            "-y",
            *inputs,
            "-filter_complex",
            filter_graph,
            "-map",
            "[outv]",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(OUTPUT_VIDEO),
        ]
    )


def main() -> None:
    if not BASE_VIDEO.exists():
        raise FileNotFoundError(BASE_VIDEO)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    clips = build_clips(ffmpeg)
    compose(ffmpeg, clips)
    print(OUTPUT_VIDEO)


if __name__ == "__main__":
    main()
