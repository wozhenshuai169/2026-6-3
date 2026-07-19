"""Build a lip-sync frame by blending only the generated mouth region.

The image model is used for the semantic mouth edit.  This helper keeps every
pixel outside a feathered mouth ellipse from the approved source artwork and
also restores the source alpha channel exactly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = tuple(int(part.strip()) for part in value.split(","))
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("box must be left,top,right,bottom")
    left, top, right, bottom = parts
    if right <= left or bottom <= top:
        raise argparse.ArgumentTypeError("box must have a positive width and height")
    return parts


def build_frame(
    source_path: Path,
    generated_path: Path,
    output_path: Path,
    mouth_box: tuple[int, int, int, int],
    feather: float,
) -> None:
    source = Image.open(source_path)
    source_mode = source.mode
    source_rgba = source.convert("RGBA")
    generated = Image.open(generated_path).convert("RGBA")
    if generated.size != source_rgba.size:
        generated = generated.resize(source_rgba.size, Image.Resampling.LANCZOS)

    mask = Image.new("L", source_rgba.size, 0)
    ImageDraw.Draw(mask).ellipse(mouth_box, fill=255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))

    result = Image.composite(generated, source_rgba, mask)
    if "A" in source_rgba.getbands():
        result.putalpha(source_rgba.getchannel("A"))
    if source_mode == "RGB":
        result = result.convert("RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mouth-box", type=parse_box, required=True)
    parser.add_argument("--feather", type=float, default=12.0)
    args = parser.parse_args()
    build_frame(args.source, args.generated, args.output, args.mouth_box, args.feather)


if __name__ == "__main__":
    main()
