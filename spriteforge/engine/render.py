"""Rendering engine for Spriteforge."""

import json
import math
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image

from .raster import (
    hex_to_rgba, in_bounds, draw_line, draw_thick_line, capsule_fill,
    rect_stroke, rect_fill, ellipse_fill, ellipse_stroke,
    gradient_radial, gradient_linear, color_replace, mask_layer_fn,
    outline_layer, draw_bezier, dither_rect, draw_poly, flood_fill
)
from .layers import (
    merge_layers, ensure_layer, inset_fill_on_mask,
    outline_from_mask, shade_band, noise_points
)


def render_frame(ops: List[List[Any]], w: int, h: int) -> List[int]:
    """
    Render a single frame from operations.
    
    Returns a flat buffer of palette indices.
    """
    layers: Dict[str, List[int]] = {"base": [0] * (w * h)}
    layer_order: List[str] = ["base"]
    current = "base"

    def merged() -> List[int]:
        return merge_layers(layers, layer_order, w, h)

    for op in ops:
        name = op[0]

        if name == "clear":
            c = int(op[1])
            for k in list(layers.keys()):
                layers[k] = [c] * (w * h)

        elif name == "layer_begin":
            current = str(op[1])
            ensure_layer(layers, layer_order, current, w, h)

        elif name == "layer_end":
            current = "base"

        elif name == "layer_merge":
            target = str(op[1]) if len(op) > 1 else "base"
            m = merged()
            layers = {target: m}
            layer_order = [target]
            current = target

        elif name == "pixel":
            c, x, y = map(int, op[1:4])
            buf = ensure_layer(layers, layer_order, current, w, h)
            if in_bounds(x, y, w, h):
                buf[y * w + x] = c

        elif name == "line":
            c, x0, y0, x1, y1 = map(int, op[1:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            draw_line(buf, w, h, c, x0, y0, x1, y1)

        elif name == "thick_line":
            c, x0, y0, x1, y1, t = map(int, op[1:7])
            buf = ensure_layer(layers, layer_order, current, w, h)
            draw_thick_line(buf, w, h, c, x0, y0, x1, y1, t)

        elif name == "capsule_fill":
            c, x0, y0, x1, y1, r = map(int, op[1:7])
            buf = ensure_layer(layers, layer_order, current, w, h)
            capsule_fill(buf, w, h, c, x0, y0, x1, y1, r)

        elif name == "rect":
            c, x, y, rw, rh = map(int, op[1:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            rect_stroke(buf, w, h, c, x, y, rw, rh)

        elif name == "rect_fill":
            c, x, y, rw, rh = map(int, op[1:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            rect_fill(buf, w, h, c, x, y, rw, rh)

        elif name == "rect_stroke":
            c, x, y, rw, rh = map(int, op[1:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            rect_stroke(buf, w, h, c, x, y, rw, rh)

        elif name == "ellipse_fill":
            c, cx, cy, rx, ry = map(int, op[1:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            ellipse_fill(buf, w, h, c, cx, cy, rx, ry)

        elif name == "ellipse_stroke":
            c, cx, cy, rx, ry = map(int, op[1:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            ellipse_stroke(buf, w, h, c, cx, cy, rx, ry)

        elif name == "gradient_radial":
            indices = [int(x) for x in op[1].split(",")] if isinstance(op[1], str) else [int(op[1])]
            cx, cy, r = map(int, op[2:5])
            buf = ensure_layer(layers, layer_order, current, w, h)
            gradient_radial(buf, w, h, indices, cx, cy, r)

        elif name == "gradient_linear":
            indices = [int(x) for x in op[1].split(",")] if isinstance(op[1], str) else [int(op[1])]
            x0, y0, x1, y1 = map(int, op[2:6])
            buf = ensure_layer(layers, layer_order, current, w, h)
            gradient_linear(buf, w, h, indices, x0, y0, x1, y1)

        elif name == "color_replace":
            old_c, new_c = map(int, op[1:3])
            layer_mask_name = str(op[3]) if len(op) > 3 else None
            mask = layers.get(layer_mask_name) if layer_mask_name else None
            buf = ensure_layer(layers, layer_order, current, w, h)
            color_replace(buf, w, h, old_c, new_c, mask)

        elif name == "mask_layer":
            mask_name = str(op[1])
            mask = layers.get(mask_name)
            if mask:
                buf = ensure_layer(layers, layer_order, current, w, h)
                mask_layer_fn(buf, mask)

        elif name == "outline_layer":
            color = int(op[1])
            thickness = int(op[2]) if len(op) > 2 else 1
            buf = ensure_layer(layers, layer_order, current, w, h)
            outline_layer(buf, w, h, thickness, color)

        elif name == "circle_fill":
            c, cx, cy, r = map(int, op[1:5])
            buf = ensure_layer(layers, layer_order, current, w, h)
            ellipse_fill(buf, w, h, c, cx, cy, r, r)

        elif name == "bezier":
            c, x0, y0, cx, cy, x1, y1 = map(int, op[1:8])
            buf = ensure_layer(layers, layer_order, current, w, h)
            draw_bezier(buf, w, h, c, x0, y0, cx, cy, x1, y1)

        elif name == "dither_rect":
            c, x, y, rw, rh = map(int, op[1:6])
            pattern = str(op[6]) if len(op) > 6 else "checker"
            buf = ensure_layer(layers, layer_order, current, w, h)
            dither_rect(buf, w, h, c, x, y, rw, rh, pattern)

        elif name == "mirror":
            axis = str(op[1]) if len(op) > 1 else "x"
            buf = ensure_layer(layers, layer_order, current, w, h)
            if axis == "x":
                for y in range(h):
                    row = y * w
                    for x in range(w // 2):
                        buf[row + (w - 1 - x)] = buf[row + x]
            elif axis == "y":
                for x in range(w):
                    for y in range(h // 2):
                        buf[(h - 1 - y) * w + x] = buf[y * w + x]

        elif name == "copy_layer":
            src_name = str(op[1])
            dst_name = str(op[2])
            src = layers.get(src_name)
            if src:
                layers[dst_name] = src[:]
                if dst_name not in layer_order:
                    layer_order.append(dst_name)

        elif name == "translate":
            dx, dy = map(int, op[1:3])
            buf = ensure_layer(layers, layer_order, current, w, h)
            old = buf[:]
            for i in range(len(buf)):
                buf[i] = 0
            for y in range(h):
                for x in range(w):
                    sx, sy = x - dx, y - dy
                    if 0 <= sx < w and 0 <= sy < h:
                        buf[y * w + x] = old[sy * w + sx]

        elif name == "rotate":
            angle_deg = float(op[1])
            cx = float(op[2]) if len(op) > 2 else w / 2
            cy = float(op[3]) if len(op) > 3 else h / 2
            angle = math.radians(angle_deg)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            buf = ensure_layer(layers, layer_order, current, w, h)
            old = buf[:]
            for i in range(len(buf)):
                buf[i] = 0
            for y in range(h):
                for x in range(w):
                    tx, ty = x - cx, y - cy
                    sx = int(round(tx * cos_a + ty * sin_a + cx))
                    sy = int(round(-tx * sin_a + ty * cos_a + cy))
                    if 0 <= sx < w and 0 <= sy < h:
                        buf[y * w + x] = old[sy * w + sx]

        elif name == "poly_fill":
            c = int(op[1])
            points = []
            for i in range(2, len(op), 2):
                points.append((float(op[i]), float(op[i + 1])))
            buf = ensure_layer(layers, layer_order, current, w, h)
            draw_poly(buf, w, h, c, points)

        elif name == "fill":
            c, x, y = map(int, op[1:4])
            buf = ensure_layer(layers, layer_order, current, w, h)
            flood_fill(buf, w, h, c, x, y)

        elif name == "inset_fill":
            c, x, y, rw, rh, inset = map(int, op[1:7])
            buf = ensure_layer(layers, layer_order, current, w, h)
            mask = merged()
            inset_fill_on_mask(buf, mask, w, h, c, x, y, rw, rh, inset)

        elif name == "shade_band":
            c = int(op[1])
            layer_name = str(op[2])
            side = str(op[3])
            thickness = int(op[4]) if len(op) > 4 else 1
            buf = ensure_layer(layers, layer_order, current, w, h)
            mask = layers.get(layer_name)
            if mask is None:
                raise ValueError(f"shade_band refers to missing layer '{layer_name}'")
            shade_band(buf, mask, w, h, c, side, thickness)

        elif name == "noise_points":
            c = int(op[1])
            layer_name = str(op[2])
            count = int(op[3])
            seed = int(op[4])
            buf = ensure_layer(layers, layer_order, current, w, h)
            mask = layers.get(layer_name)
            if mask is None:
                raise ValueError(f"noise_points refers to missing layer '{layer_name}'")
            noise_points(buf, mask, w, h, c, count, seed)

        elif name == "outline":
            outline_color = int(op[1])
            thickness = int(op[2]) if len(op) > 2 else 1
            buf = ensure_layer(layers, layer_order, current, w, h)
            m = merged()
            mask = [1 if v != 0 else 0 for v in m]
            outline_from_mask(buf, mask, w, h, outline_color, thickness)

        else:
            raise ValueError(f"Unknown op: {name}")

    return merged()


def buf_to_image(buf: List[int], w: int, h: int, palette_rgba: List[Tuple[int, int, int, int]]) -> Image.Image:
    """Convert a palette-indexed buffer to a PIL Image."""
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            idx = buf[y * w + x]
            px[x, y] = palette_rgba[idx]
    return img


def process_frame_inheritance(raw_frames: List[Dict[str, Any]]) -> List[List[List[Any]]]:
    """Process frame inheritance and return list of ops for each frame."""
    processed_ops = []

    for i, fr in enumerate(raw_frames):
        if "base" in fr:
            base_idx = int(fr["base"])
            base_ops = list(processed_ops[base_idx])
            if "overrides" in fr:
                for override in fr["overrides"]:
                    op_idx = override.get("op_index")
                    if op_idx is not None and op_idx < len(base_ops):
                        base_ops[op_idx] = override["op"]
            if "append_ops" in fr:
                base_ops.extend(fr["append_ops"])
            processed_ops.append(base_ops)
        else:
            processed_ops.append(fr["ops"])

    return processed_ops


def render_sprite(
    data: Dict[str, Any],
    outdir: Path,
    scale: int = 1,
    layout: str = "horizontal",
    cols: int = 4,
    export_frames: bool = False,
    export_gif: bool = False
) -> Dict[str, Any]:
    """
    Render a complete sprite from spriteops data.
    
    Returns metadata about the rendered sprite.
    """
    w = int(data["canvas"]["w"])
    h = int(data["canvas"]["h"])
    palette_rgba = [hex_to_rgba(c) for c in data["palette"]]

    # Process frames with inheritance support
    raw_frames = data["frames"]
    processed_ops = process_frame_inheritance(raw_frames)

    # Render all frames
    frames: List[Image.Image] = []
    frame_durations: List[int] = []

    for i, ops in enumerate(processed_ops):
        buf = render_frame(ops, w, h)
        img = buf_to_image(buf, w, h, palette_rgba)
        frames.append(img)
        duration = raw_frames[i].get("durationMs", 100)
        frame_durations.append(duration)

        # Save individual frames if requested
        if export_frames:
            img_scaled = img.resize((w * scale, h * scale), resample=Image.NEAREST)
            img_scaled.save(outdir / f"frame_{i:02d}.png")

    # Generate sprite sheet
    if layout == "horizontal":
        sheet = Image.new("RGBA", (w * len(frames), h))
        for i, img in enumerate(frames):
            sheet.paste(img, (i * w, 0))
    else:  # grid
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGBA", (w * cols, h * rows))
        for i, img in enumerate(frames):
            col = i % cols
            row = i // cols
            sheet.paste(img, (col * w, row * h))

    sheet_scaled = sheet.resize((sheet.width * scale, sheet.height * scale), resample=Image.NEAREST)
    
    # Determine base name from data or use default
    base_name = data.get("name", "sprite")
    
    sheet_scaled.save(outdir / f"{base_name}_sheet.png")

    # Generate animated GIF if requested and multiple frames
    if export_gif and len(frames) > 1:
        gif_frames = [img.resize((w * scale, h * scale), resample=Image.NEAREST) for img in frames]
        gif_frames[0].save(
            outdir / f"{base_name}.gif",
            save_all=True,
            append_images=gif_frames[1:],
            duration=frame_durations,
            loop=0,
            disposal=2
        )

    # Generate animation metadata
    animations = data.get("animations", {})
    anim_meta = {
        "sprite": base_name,
        "frameWidth": w,
        "frameHeight": h,
        "totalFrames": len(frames),
        "scale": scale,
        "layout": layout,
        "animations": {}
    }
    
    for anim_name, anim_data in animations.items():
        frame_indices = anim_data.get("frames", [0])
        anim_meta["animations"][anim_name] = {
            "frames": frame_indices,
            "loop": anim_data.get("loop", True),
            "frameDurations": [frame_durations[f] for f in frame_indices if f < len(frame_durations)]
        }

    with open(outdir / f"{base_name}_meta.json", "w", encoding="utf-8") as f:
        json.dump(anim_meta, f, indent=2)

    return anim_meta

