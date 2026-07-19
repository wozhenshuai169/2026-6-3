from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
CAPTURES = WORK / "captures-latest"
MANIFEST = WORK / "video_manifest.json"
BUILD = WORK / "build"
SLIDES = BUILD / "slides"
AUDIO = BUILD / "audio"
SEGMENTS = BUILD / "segments"
OUTPUT = WORK / "云游智导_三端全功能演示_7分钟.mp4"
SUBTITLES = WORK / "云游智导_三端全功能演示_字幕.srt"
CONTACT_SHEET = WORK / "录制画面总览.jpg"

VIDEO_TOOLS = Path.home() / ".cache" / "codex-video-tools"
VOICE_DIR = Path.home() / ".cache" / "codex-video-voices"
VOICE_MODEL = VOICE_DIR / "zh_CN-huayan-medium.onnx"
VOICE_CONFIG = VOICE_DIR / "zh_CN-huayan-medium.onnx.json"
if str(VIDEO_TOOLS) not in sys.path:
    sys.path.insert(0, str(VIDEO_TOOLS))

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
    import imageio_ffmpeg
except ImportError as exc:
    raise SystemExit(f"缺少视频制作依赖：{exc}") from exc


WIDTH = 1920
HEIGHT = 1080
FPS = 24
BG = "#F4F0E8"
PAPER = "#FFFDF9"
INK = "#25211D"
MUTED = "#766F67"
ACCENT = "#C75E42"
GREEN = "#34765F"
LINE = "#E7DED2"


def find_font(candidates: list[str]) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError("未找到可用中文字体")


FONT_REGULAR = find_font(
    [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
)
FONT_BOLD = find_font(
    [
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        str(FONT_REGULAR),
    ]
)


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size=size)


def run(command: list[str], cwd: Path | None = None) -> None:
    print(" ".join(str(item) for item in command))
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def contain(image: Image.Image, size: tuple[int, int], color: str = BG) -> Image.Image:
    canvas = Image.new("RGB", size, color)
    fitted = ImageOps.contain(image.convert("RGB"), size, Image.Resampling.LANCZOS)
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    text_font,
    fill: str,
    max_width: int,
    spacing: int,
) -> int:
    x, y = xy
    line_height = text_font.size + spacing
    for line in wrap_text(draw, text, text_font, max_width):
        draw.text((x, y), line, font=text_font, fill=fill)
        y += line_height
    return y


def warm_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    pixels = image.load()
    for y in range(HEIGHT):
        ratio = y / max(HEIGHT - 1, 1)
        r = int(247 - 7 * ratio)
        g = int(244 - 8 * ratio)
        b = int(238 - 10 * ratio)
        for x in range(WIDTH):
            pixels[x, y] = (r, g, b)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((1420, -360, 2160, 380), fill=(199, 94, 66, 24))
    d.ellipse((-260, 760, 420, 1440), fill=(52, 118, 95, 18))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def phone_crop(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGB")
    if source.size == (1280, 720):
        left = (source.width - 390) // 2
        return source.crop((left, 0, left + 390, 720))
    # Fallback: find the non-background bounding box and keep the central device.
    corner = Image.new("RGB", source.size, source.getpixel((0, 0)))
    difference = ImageChops.difference(source, corner).convert("L")
    bbox = difference.point(lambda value: 255 if value > 8 else 0).getbbox()
    if bbox:
        return source.crop(bbox)
    return source


def paste_with_shadow(base: Image.Image, image: Image.Image, xy: tuple[int, int], radius: int = 30) -> None:
    x, y = xy
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.rounded_rectangle(
        (x + 16, y + 22, x + image.width + 16, y + image.height + 22),
        radius=radius,
        fill=(48, 36, 27, 72),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(shadow)
    mask = Image.new("L", image.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
    base.paste(image.convert("RGBA"), (x, y), mask)


def draw_brand(draw: ImageDraw.ImageDraw, section: str, index: int, total: int) -> None:
    draw.rounded_rectangle((82, 58, 132, 108), radius=15, fill=ACCENT)
    draw.polygon([(96, 91), (107, 73), (118, 91)], fill=PAPER)
    draw.text((148, 62), "云游智导", font=font(28, True), fill=INK)
    draw.text((148, 94), "LINGSHAN INTELLIGENT GUIDE", font=font(12), fill=MUTED)
    chip_font = font(20, True)
    chip_w = draw.textbbox((0, 0), section, font=chip_font)[2] + 42
    draw.rounded_rectangle((WIDTH - chip_w - 82, 64, WIDTH - 82, 108), radius=22, fill="#EDE5DA")
    draw.text((WIDTH - chip_w - 61, 73), section, font=chip_font, fill=ACCENT)

    progress_left = 82
    progress_right = WIDTH - 82
    progress_y = HEIGHT - 34
    draw.rounded_rectangle((progress_left, progress_y, progress_right, progress_y + 5), radius=3, fill="#DED4C8")
    progress = progress_left + (progress_right - progress_left) * ((index + 1) / total)
    draw.rounded_rectangle((progress_left, progress_y, int(progress), progress_y + 5), radius=3, fill=ACCENT)
    draw.text((progress_right - 86, progress_y - 28), f"{index + 1:02d} / {total:02d}", font=font(14), fill=MUTED)


def draw_copy(draw: ImageDraw.ImageDraw, scene: dict, left: int = 100, width: int = 980) -> None:
    draw.text((left, 176), scene["title"], font=font(62, True), fill=INK)
    y = draw_wrapped(draw, (left, 262), scene["subtitle"], font(25), ACCENT, width, 12)
    draw.rounded_rectangle((left, y + 18, left + 92, y + 24), radius=3, fill=ACCENT)
    y += 72
    for bullet_index, bullet in enumerate(scene.get("bullets", []), 1):
        draw.rounded_rectangle((left, y - 4, left + 46, y + 42), radius=14, fill="#EDE5DA")
        number = str(bullet_index)
        number_box = draw.textbbox((0, 0), number, font=font(18, True))
        number_x = left + 23 - (number_box[2] - number_box[0]) // 2
        draw.text((number_x, y + 6), number, font=font(18, True), fill=ACCENT)
        y = draw_wrapped(draw, (left + 66, y), bullet, font(27), INK, width - 66, 14) + 24


def make_opening_slide(scene: dict, capture: Path, index: int, total: int) -> Image.Image:
    source = Image.open(capture).convert("RGB")
    source = ImageOps.fit(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    result = source.convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(HEIGHT):
        alpha = int(25 + 120 * (y / HEIGHT) ** 2)
        d.line((0, y, WIDTH, y), fill=(24, 18, 14, alpha))
    d.rounded_rectangle((108, 730, 1090, 996), radius=32, fill=(28, 23, 20, 190))
    d.text((150, 770), scene["title"], font=font(62, True), fill="#FFFFFF")
    d.text((150, 854), scene["subtitle"], font=font(28), fill="#F4D9CC")
    d.rounded_rectangle((150, 916, 258, 924), radius=4, fill="#E98765")
    result = Image.alpha_composite(result, overlay)
    draw = ImageDraw.Draw(result)
    draw_brand(draw, scene["section"], index, total)
    return result.convert("RGB")


def make_landing_slide(scene: dict, capture: Path, index: int, total: int) -> Image.Image:
    source = Image.open(capture).convert("RGB")
    source = ImageOps.fit(source, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    result = source.convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle((1130, 118, 1840, 330), radius=28, fill=(255, 253, 249, 226), outline=(231, 222, 210, 255), width=2)
    d.text((1180, 158), scene["title"], font=font(46, True), fill=INK)
    d.text((1180, 230), scene["subtitle"], font=font(22), fill=ACCENT)
    result = Image.alpha_composite(result, overlay)
    draw = ImageDraw.Draw(result)
    draw_brand(draw, scene["section"], index, total)
    return result.convert("RGB")


def make_compare_slide(scene: dict, capture: Path, secondary: Path, index: int, total: int) -> Image.Image:
    base = warm_background().convert("RGBA")
    draw = ImageDraw.Draw(base)
    draw_brand(draw, scene["section"], index, total)
    draw_copy(draw, scene, left=82, width=650)
    first = phone_crop(secondary)
    second = phone_crop(capture)
    target_h = 825
    target_w = int(first.width * target_h / first.height)
    first = first.resize((target_w, target_h), Image.Resampling.LANCZOS)
    second = second.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x1, x2, y = 860, 1375, 154
    paste_with_shadow(base, first, (x1, y), radius=27)
    paste_with_shadow(base, second, (x2, y), radius=27)
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((x1 + 92, 120, x1 + target_w - 92, 158), radius=18, fill="#312C27")
    draw.rounded_rectangle((x2 + 92, 120, x2 + target_w - 92, 158), radius=18, fill=GREEN)
    draw.text((x1 + 123, 128), "暂停提问", font=font(15, True), fill="#FFFFFF")
    draw.text((x2 + 121, 128), "自然续讲", font=font(15, True), fill="#FFFFFF")
    return base.convert("RGB")


def make_standard_slide(scene: dict, capture: Path, index: int, total: int) -> Image.Image:
    base = warm_background().convert("RGBA")
    draw = ImageDraw.Draw(base)
    draw_brand(draw, scene["section"], index, total)
    draw_copy(draw, scene, left=100, width=1030)

    phone = phone_crop(capture)
    target_h = 952
    target_w = int(phone.width * target_h / phone.height)
    phone = phone.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = WIDTH - target_w - 130
    y = 70
    paste_with_shadow(base, phone, (x, y), radius=32)
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((x + 135, 32, x + target_w - 135, 70), radius=19, fill="#312C27")
    label = "功能实录"
    box = draw.textbbox((0, 0), label, font=font(15, True))
    draw.text((x + target_w // 2 - box[2] // 2, 41), label, font=font(15, True), fill="#FFFFFF")
    return base.convert("RGB")


def build_slides(scenes: list[dict]) -> list[Path]:
    SLIDES.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, scene in enumerate(scenes):
        capture = CAPTURES / scene["image"]
        if not capture.exists():
            raise FileNotFoundError(capture)
        style = scene.get("style", "standard")
        if style == "opening":
            slide = make_opening_slide(scene, capture, index, len(scenes))
        elif style == "landing":
            slide = make_landing_slide(scene, capture, index, len(scenes))
        elif style == "compare":
            slide = make_compare_slide(scene, capture, CAPTURES / scene["secondaryImage"], index, len(scenes))
        else:
            slide = make_standard_slide(scene, capture, index, len(scenes))
        path = SLIDES / f"scene-{index:02d}.png"
        slide.save(path, quality=95)
        paths.append(path)
    return paths


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as stream:
        return stream.getnframes() / float(stream.getframerate())


def atempo_chain(ratio: float) -> str:
    filters: list[str] = []
    while ratio > 2.0:
        filters.append("atempo=2.0")
        ratio /= 2.0
    while ratio < 0.5:
        filters.append("atempo=0.5")
        ratio /= 0.5
    filters.append(f"atempo={ratio:.5f}")
    return ",".join(filters)


def synthesize_audio(scenes: list[dict], ffmpeg: str) -> list[dict]:
    if not VOICE_MODEL.exists() or not VOICE_CONFIG.exists():
        raise FileNotFoundError("本地中文语音模型不存在")
    AUDIO.mkdir(parents=True, exist_ok=True)
    details: list[dict] = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(VIDEO_TOOLS)
    env["PYTHONUTF8"] = "1"

    for index, scene in enumerate(scenes):
        text_path = AUDIO / f"scene-{index:02d}.txt"
        raw_path = AUDIO / f"scene-{index:02d}-raw.wav"
        padded_path = AUDIO / f"scene-{index:02d}.wav"
        text_path.write_text(scene["narration"], encoding="utf-8")
        command = [
            sys.executable,
            "-m",
            "piper",
            "-m",
            str(VOICE_MODEL),
            "-c",
            str(VOICE_CONFIG),
            "-i",
            str(text_path),
            "-f",
            str(raw_path),
            "--length-scale",
            "0.90",
            "--sentence-silence",
            "0.16",
            "--volume",
            "0.95",
        ]
        print(f"生成旁白 {index + 1:02d}/{len(scenes)}")
        subprocess.run(command, env=env, check=True)
        raw_duration = wav_duration(raw_path)
        max_voice = scene["duration"] - 1.4
        ratio = raw_duration / max_voice if raw_duration > max_voice else 1.0
        filters = []
        if ratio > 1.001:
            filters.append(atempo_chain(ratio))
        filters.extend(["adelay=700", f"apad=pad_dur={scene['duration']}"])
        run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(raw_path),
                "-af",
                ",".join(filters),
                "-t",
                str(scene["duration"]),
                "-ar",
                "24000",
                "-ac",
                "1",
                str(padded_path),
            ]
        )
        effective_voice = min(raw_duration / ratio, max_voice)
        details.append({"raw": raw_duration, "ratio": ratio, "voice": effective_voice, "path": padded_path})
    return details


def timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_caption(text: str, max_chars: int = 22) -> list[str]:
    chunks = [item.strip() for item in re.split(r"(?<=[。！？；])", text) if item.strip()]
    result: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars * 2:
            result.append(chunk)
            continue
        current = ""
        for piece in re.split(r"(?<=[，、：])", chunk):
            if current and len(current + piece) > max_chars * 2:
                result.append(current)
                current = piece
            else:
                current += piece
        if current:
            result.append(current)
    return result or [text]


def build_subtitles(scenes: list[dict], audio_details: list[dict]) -> None:
    entries: list[str] = []
    counter = 1
    scene_start = 0.0
    for scene, audio in zip(scenes, audio_details):
        captions = split_caption(scene["narration"])
        weights = [max(1, len(re.sub(r"\s", "", caption))) for caption in captions]
        voice_start = scene_start + 0.72
        voice_duration = max(1.0, audio["voice"])
        cursor = voice_start
        for caption, weight in zip(captions, weights):
            duration = voice_duration * weight / sum(weights)
            end = min(cursor + duration, scene_start + scene["duration"] - 0.3)
            wrapped = "\n".join([caption[i : i + 22] for i in range(0, len(caption), 22)])
            entries.append(f"{counter}\n{timestamp(cursor)} --> {timestamp(end)}\n{wrapped}\n")
            counter += 1
            cursor = end
        scene_start += scene["duration"]
    SUBTITLES.write_text("\n".join(entries), encoding="utf-8")


def build_segments(scenes: list[dict], slides: list[Path], audio_details: list[dict], ffmpeg: str) -> list[Path]:
    SEGMENTS.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, (scene, slide, audio) in enumerate(zip(scenes, slides, audio_details)):
        path = SEGMENTS / f"scene-{index:02d}.mp4"
        fade_out = max(0.0, scene["duration"] - 0.28)
        vf = f"scale={WIDTH}:{HEIGHT},fade=t=in:st=0:d=0.24,fade=t=out:st={fade_out:.2f}:d=0.28,format=yuv420p"
        run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-framerate",
                str(FPS),
                "-i",
                str(slide),
                "-i",
                str(audio["path"]),
                "-t",
                str(scene["duration"]),
                "-vf",
                vf,
                "-r",
                str(FPS),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-tune",
                "stillimage",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-shortest",
                str(path),
            ]
        )
        paths.append(path)
    return paths


def concat_and_burn(segment_paths: list[Path], ffmpeg: str) -> None:
    concat_file = BUILD / "concat.txt"
    base_video = BUILD / "video-with-audio.mp4"
    concat_file.write_text(
        "\n".join("file '" + str(path.resolve()).replace("'", "'\\''") + "'" for path in segment_paths),
        encoding="utf-8",
    )
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(base_video)])

    subtitle_filter = (
        "subtitles=云游智导_三端全功能演示_字幕.srt:"
        "force_style='FontName=Microsoft YaHei,FontSize=21,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H90000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=42'"
    )
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(base_video),
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ],
        cwd=WORK,
    )


def build_contact_sheet(slides: list[Path], scenes: list[dict]) -> None:
    thumb_w, thumb_h = 480, 270
    cols = 3
    rows = math.ceil(len(slides) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 42)), "#DDD6CC")
    draw = ImageDraw.Draw(sheet)
    for index, (slide_path, scene) in enumerate(zip(slides, scenes)):
        thumb = Image.open(slide_path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + 42)
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + 42), fill="#2F2A26")
        draw.text((x + 12, y + thumb_h + 9), f"{index + 1:02d}  {scene['title']}", font=font(16, True), fill="#FFFFFF")
    sheet.save(CONTACT_SHEET, quality=91)


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    scenes = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total_duration = sum(float(scene["duration"]) for scene in scenes)
    if len(scenes) != 18 or abs(total_duration - 420.0) > 0.01:
        raise ValueError(f"分镜应为 18 段、总时长 420 秒，当前为 {len(scenes)} 段、{total_duration} 秒")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"FFmpeg: {ffmpeg}")
    slides = build_slides(scenes)
    build_contact_sheet(slides, scenes)
    audio_details = synthesize_audio(scenes, ffmpeg)
    build_subtitles(scenes, audio_details)
    segments = build_segments(scenes, slides, audio_details, ffmpeg)
    concat_and_burn(segments, ffmpeg)
    print(f"完成：{OUTPUT}")


if __name__ == "__main__":
    main()
