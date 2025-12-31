"""Layer management and helper functions for Spriteforge."""

from typing import Dict, List


def merge_layers(layers: Dict[str, List[int]], layer_order: List[str], w: int, h: int) -> List[int]:
    """Merge all layers in order, with non-zero pixels overwriting."""
    out = [0] * (w * h)
    for lname in layer_order:
        src = layers.get(lname)
        if src is None:
            continue
        for i, v in enumerate(src):
            if v != 0:  # 0 treated as transparent
                out[i] = v
    return out


def ensure_layer(layers: Dict[str, List[int]], layer_order: List[str], name: str, w: int, h: int) -> List[int]:
    """Ensure a layer exists, creating it if necessary."""
    if name not in layers:
        layers[name] = [0] * (w * h)
        layer_order.append(name)
    return layers[name]


def inset_fill_on_mask(dest: List[int], mask: List[int], w: int, h: int, color: int, x: int, y: int, rw: int, rh: int, inset: int) -> None:
    """Fill a rectangle with inset, only where mask is non-zero."""
    x0 = x + inset
    y0 = y + inset
    x1 = x + rw - inset - 1
    y1 = y + rh - inset - 1
    for yy in range(y0, y1 + 1):
        if 0 <= yy < h:
            row = yy * w
            for xx in range(x0, x1 + 1):
                if 0 <= xx < w:
                    idx = row + xx
                    if mask[idx] != 0:
                        dest[idx] = color


def outline_from_mask(dest: List[int], mask: List[int], w: int, h: int, outline_color: int, thickness: int = 1) -> None:
    """Create an outline around non-zero mask pixels."""
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
            dest[idx] = outline_color
            work[idx] = 1


def shade_band(dest: List[int], mask: List[int], w: int, h: int, shade_color: int, side: str, thickness: int = 1) -> None:
    """Add shading band along edges of masked area."""
    side = str(side).lower()
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            if mask[idx] == 0:
                continue

            if side == "right":
                near = False
                for t in range(1, thickness + 1):
                    nx = x + t
                    if nx >= w or mask[y * w + nx] == 0:
                        near = True
                        break
                if near:
                    dest[idx] = shade_color

            elif side == "bottom":
                near = False
                for t in range(1, thickness + 1):
                    ny = y + t
                    if ny >= h or mask[ny * w + x] == 0:
                        near = True
                        break
                if near:
                    dest[idx] = shade_color

            elif side == "top_left":
                near = False
                for t in range(1, thickness + 1):
                    if y - t < 0 or mask[(y - t) * w + x] == 0:
                        near = True
                        break
                    if x - t < 0 or mask[y * w + (x - t)] == 0:
                        near = True
                        break
                if near:
                    dest[idx] = shade_color

            elif side == "edge":
                boundary = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or mask[ny * w + nx] == 0:
                        boundary = True
                        break
                if boundary:
                    dest[idx] = shade_color
            else:
                raise ValueError(f"shade_band side unsupported: {side}")


def noise_points(dest: List[int], mask: List[int], w: int, h: int, color: int, count: int, seed: int) -> None:
    """Add deterministic noise points within masked area."""
    eligible = [i for i, v in enumerate(mask) if v != 0]
    if not eligible or count <= 0:
        return
    x = seed & 0x7FFFFFFF
    for _ in range(count):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        idx = eligible[x % len(eligible)]
        dest[idx] = color

