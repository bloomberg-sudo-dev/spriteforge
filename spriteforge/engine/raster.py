"""Low-level raster drawing primitives for Spriteforge."""

import math
from collections import deque
from typing import List, Tuple, Optional


def hex_to_rgba(h: str) -> Tuple[int, int, int, int]:
    """Convert hex color string to RGBA tuple."""
    h = h.lstrip("#")
    if len(h) == 8:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        a = int(h[6:8], 16)
        return (r, g, b, a)
    if len(h) == 6:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return (r, g, b, 255)
    raise ValueError(f"Bad color: {h}")


def in_bounds(x: int, y: int, w: int, h: int) -> bool:
    """Check if coordinates are within buffer bounds."""
    return 0 <= x < w and 0 <= y < h


def draw_line(buf: List[int], w: int, h: int, color: int, x0: int, y0: int, x1: int, y1: int) -> None:
    """Draw a line using Bresenham's algorithm."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        if in_bounds(x, y, w, h):
            buf[y * w + x] = color
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def draw_thick_line(buf: List[int], w: int, h: int, color: int, x0: int, y0: int, x1: int, y1: int, thickness: int) -> None:
    """Draw a thick line by drawing circles along the path."""
    if thickness <= 1:
        draw_line(buf, w, h, color, x0, y0, x1, y1)
        return
    dx = x1 - x0
    dy = y1 - y0
    dist = math.sqrt(dx * dx + dy * dy)
    if dist == 0:
        ellipse_fill(buf, w, h, color, x0, y0, thickness // 2, thickness // 2)
        return
    steps = int(dist * 2)
    for i in range(steps + 1):
        t = i / steps
        tx = x0 + t * dx
        ty = y0 + t * dy
        ellipse_fill(buf, w, h, color, int(round(tx)), int(round(ty)), thickness // 2, thickness // 2)


def capsule_fill(buf: List[int], w: int, h: int, color: int, x0: int, y0: int, x1: int, y1: int, r: int) -> None:
    """Draw a capsule (thick line with radius r)."""
    draw_thick_line(buf, w, h, color, x0, y0, x1, y1, r * 2)


def rect_stroke(buf: List[int], w: int, h: int, color: int, x: int, y: int, rw: int, rh: int) -> None:
    """Draw a rectangle outline."""
    for i in range(rw):
        if in_bounds(x + i, y, w, h):
            buf[y * w + (x + i)] = color
        if in_bounds(x + i, y + rh - 1, w, h):
            buf[(y + rh - 1) * w + (x + i)] = color
    for j in range(rh):
        if in_bounds(x, y + j, w, h):
            buf[(y + j) * w + x] = color
        if in_bounds(x + rw - 1, y + j, w, h):
            buf[(y + j) * w + (x + rw - 1)] = color


def rect_fill(buf: List[int], w: int, h: int, color: int, x: int, y: int, rw: int, rh: int) -> None:
    """Draw a filled rectangle."""
    for yy in range(y, y + rh):
        if 0 <= yy < h:
            row = yy * w
            for xx in range(x, x + rw):
                if 0 <= xx < w:
                    buf[row + xx] = color


def ellipse_fill(buf: List[int], w: int, h: int, color: int, cx: int, cy: int, rx: int, ry: int) -> None:
    """Draw a filled ellipse."""
    if rx <= 0 or ry <= 0:
        if rx == 0 and ry == 0:
            if in_bounds(cx, cy, w, h):
                buf[cy * w + cx] = color
        return
    for yy in range(cy - ry, cy + ry + 1):
        if not (0 <= yy < h):
            continue
        dy = (yy - cy) / ry
        inside = 1.0 - dy * dy
        if inside < 0:
            continue
        span = int(math.floor(rx * math.sqrt(inside)))
        x0 = cx - span
        x1 = cx + span
        row = yy * w
        for xx in range(x0, x1 + 1):
            if 0 <= xx < w:
                buf[row + xx] = color


def ellipse_stroke(buf: List[int], w: int, h: int, color: int, cx: int, cy: int, rx: int, ry: int) -> None:
    """Draw an ellipse outline using midpoint algorithm."""
    if rx <= 0 or ry <= 0:
        return
    x = 0
    y = ry
    rx2 = rx * rx
    ry2 = ry * ry
    two_rx2 = 2 * rx2
    two_ry2 = 2 * ry2
    px = 0
    py = two_rx2 * y

    def plot(px: int, py: int) -> None:
        for sx, sy in ((cx + px, cy + py), (cx - px, cy + py), (cx + px, cy - py), (cx - px, cy - py)):
            if in_bounds(sx, sy, w, h):
                buf[sy * w + sx] = color

    plot(x, y)
    p = round(ry2 - (rx2 * ry) + (0.25 * rx2))
    while px < py:
        x += 1
        px += two_ry2
        if p < 0:
            p += ry2 + px
        else:
            y -= 1
            py -= two_rx2
            p += ry2 + px - py
        plot(x, y)
    p = round(ry2 * (x + 0.5) * (x + 0.5) + rx2 * (y - 1) * (y - 1) - rx2 * ry2)
    while y > 0:
        y -= 1
        py -= two_rx2
        if p > 0:
            p += rx2 - py
        else:
            x += 1
            px += two_ry2
            p += rx2 - py + px
        plot(x, y)


def gradient_radial(buf: List[int], w: int, h: int, palette_indices: List[int], cx: int, cy: int, r: int) -> None:
    """Draw a radial gradient."""
    if not palette_indices or r <= 0:
        return
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if in_bounds(xx, yy, w, h):
                dist = math.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                if dist <= r:
                    t = dist / r
                    idx = int(t * (len(palette_indices) - 1))
                    buf[yy * w + xx] = palette_indices[idx]


def gradient_linear(buf: List[int], w: int, h: int, palette_indices: List[int], x0: int, y0: int, x1: int, y1: int) -> None:
    """Draw a linear gradient."""
    if not palette_indices:
        return
    dx = x1 - x0
    dy = y1 - y0
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return
    for y in range(h):
        for x in range(w):
            t = ((x - x0) * dx + (y - y0) * dy) / len_sq
            t = max(0, min(1, t))
            idx = int(t * (len(palette_indices) - 1))
            buf[y * w + x] = palette_indices[idx]


def color_replace(buf: List[int], w: int, h: int, old_c: int, new_c: int, mask_layer: Optional[List[int]] = None) -> None:
    """Replace one color with another."""
    for i in range(w * h):
        if mask_layer and mask_layer[i] == 0:
            continue
        if buf[i] == old_c:
            buf[i] = new_c


def mask_layer_fn(buf: List[int], mask: List[int]) -> None:
    """Apply a mask to a buffer (clear pixels where mask is 0)."""
    for i in range(len(buf)):
        if mask[i] == 0:
            buf[i] = 0


def outline_layer(buf: List[int], w: int, h: int, thickness: int, color: int) -> None:
    """Add an outline around non-zero pixels in the buffer."""
    mask = [1 if v != 0 else 0 for v in buf]
    work = mask[:]
    for _ in range(thickness):
        add = []
        for y in range(h):
            for x in range(w):
                idx = y * w + x
                if work[idx] != 0:
                    continue
                touch = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and work[ny * w + nx] != 0:
                        touch = True
                        break
                if touch:
                    add.append(idx)
        for idx in add:
            buf[idx] = color
            work[idx] = 1


def draw_bezier(buf: List[int], w: int, h: int, color: int, x0: int, y0: int, cx: int, cy: int, x1: int, y1: int) -> None:
    """Draw a quadratic Bezier curve."""
    steps = max(abs(x0 - x1), abs(y0 - y1), abs(x0 - cx), abs(y0 - cy), 10) * 2
    for i in range(steps + 1):
        t = i / steps
        tx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        ty = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        ix, iy = int(round(tx)), int(round(ty))
        if in_bounds(ix, iy, w, h):
            buf[iy * w + ix] = color


def dither_rect(buf: List[int], w: int, h: int, color: int, x: int, y: int, rw: int, rh: int, pattern: str = "checker") -> None:
    """Draw a dithered rectangle."""
    for yy in range(y, y + rh):
        if 0 <= yy < h:
            row = yy * w
            for xx in range(x, x + rw):
                if 0 <= xx < w:
                    if pattern == "checker":
                        if (xx + yy) % 2 == 0:
                            buf[row + xx] = color
                    elif pattern == "dots":
                        if xx % 2 == 0 and yy % 2 == 0:
                            buf[row + xx] = color


def draw_poly(buf: List[int], w: int, h: int, color: int, points: List[Tuple[float, float]]) -> None:
    """Draw a filled polygon using scanline fill."""
    if not points:
        return
    min_y = int(min(p[1] for p in points))
    max_y = int(max(p[1] for p in points))
    for y in range(min_y, max_y + 1):
        if not (0 <= y < h):
            continue
        nodes = []
        j = len(points) - 1
        for i in range(len(points)):
            if (points[i][1] < y <= points[j][1]) or (points[j][1] < y <= points[i][1]):
                if points[j][1] != points[i][1]:
                    nodes.append(points[i][0] + (y - points[i][1]) / (points[j][1] - points[i][1]) * (points[j][0] - points[i][0]))
            j = i
        nodes.sort()
        for i in range(0, len(nodes), 2):
            if i + 1 >= len(nodes):
                break
            x0 = int(math.ceil(nodes[i]))
            x1 = int(math.floor(nodes[i + 1]))
            for x in range(x0, x1 + 1):
                if 0 <= x < w:
                    buf[y * w + x] = color


def flood_fill(buf: List[int], w: int, h: int, color: int, sx: int, sy: int) -> None:
    """Flood fill starting from a point."""
    if not in_bounds(sx, sy, w, h):
        return
    target = buf[sy * w + sx]
    if target == color:
        return
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        if not in_bounds(x, y, w, h):
            continue
        idx = y * w + x
        if buf[idx] != target:
            continue
        buf[idx] = color
        q.append((x + 1, y))
        q.append((x - 1, y))
        q.append((x, y + 1))
        q.append((x, y - 1))

