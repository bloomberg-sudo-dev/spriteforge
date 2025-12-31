# Spriteforge

A deterministic, terminal-first pixel sprite compiler.

Spriteforge compiles JSON sprite definitions into spritesheets, animated GIFs, and game-engine-ready metadata. It's designed to be used as a CLI tool in your development workflow.

## Installation

```bash
# Recommended: Install with pipx for global CLI access
pipx install spriteforge

# Or install with pip
pip install spriteforge
```

## Quick Start

### Create a new sprite

```bash
spriteforge new my_hero --w 32 --h 32 --palette pico8
```

This creates `my_hero.spriteops.json` with a 32x32 canvas and the PICO-8 palette.

### Edit a sprite

```bash
spriteforge edit my_hero.spriteops.json
```

Opens the TUI editor where you can paint pixels, manage frames, and preview animations.

### Validate a sprite

```bash
spriteforge validate my_hero.spriteops.json
```

Validates the JSON structure, operation parameters, and palette references.

### Render a sprite

```bash
spriteforge render my_hero.spriteops.json --outdir dist --scale 4 --gif
```

Outputs:
- `dist/my_hero_sheet.png` - Spritesheet
- `dist/my_hero_meta.json` - Animation metadata
- `dist/my_hero.gif` - Animated preview (if multi-frame)

## CLI Reference

### `spriteforge validate <file|dir> [--strict]`

Validates spriteops JSON files.

- `--strict`: Enable strict validation (e.g., require seed for noise_points)

### `spriteforge render <file|dir>`

Renders sprites to images.

Options:
- `--outdir <dir>` (required): Output directory
- `--scale N`: Scale factor (default: 1)
- `--layout horizontal|grid`: Sheet layout (default: horizontal)
- `--cols N`: Columns for grid layout (default: 4)
- `--frames`: Export individual frames
- `--gif`: Export animated GIF

### `spriteforge new <name>`

Creates a new spriteops JSON file.

Options:
- `--w N`: Canvas width (default: 32)
- `--h N`: Canvas height (default: 32)
- `--palette <preset|colors>`: Palette preset or comma-separated hex colors

Presets: `gameboy`, `pico8`, `grayscale`, `default`

### `spriteforge edit <file>`

Opens the TUI editor.

## Spriteops Format

Spriteforge uses a JSON-based format called `spriteops`:

```json
{
  "format": "spriteops",
  "version": 1,
  "canvas": { "w": 32, "h": 32 },
  "palette": ["#00000000", "#000000", "#ffffff", ...],
  "animations": {
    "idle": { "loop": true, "frames": [0] },
    "walk": { "loop": true, "frames": [0, 1, 2, 3] }
  },
  "frames": [
    {
      "durationMs": 100,
      "ops": [
        ["clear", 0],
        ["layer_begin", "body"],
        ["rect_fill", 2, 10, 10, 12, 12],
        ["layer_end"],
        ["outline", 1, 1]
      ]
    }
  ]
}
```

### Palette

- Index 0 is always transparent
- Colors are hex strings: `#RRGGBB` or `#RRGGBBAA`

### Operations

| Operation | Parameters | Description |
|-----------|------------|-------------|
| `clear` | color | Clear canvas to color |
| `pixel` | color, x, y | Set single pixel |
| `line` | color, x0, y0, x1, y1 | Draw line |
| `rect_fill` | color, x, y, w, h | Filled rectangle |
| `ellipse_fill` | color, cx, cy, rx, ry | Filled ellipse |
| `circle_fill` | color, cx, cy, r | Filled circle |
| `poly_fill` | color, x1, y1, x2, y2, ... | Filled polygon |
| `fill` | color, x, y | Flood fill |
| `bezier` | color, x0, y0, cx, cy, x1, y1 | Bezier curve |
| `layer_begin` | name | Start named layer |
| `layer_end` | | End current layer |
| `layer_merge` | [name] | Merge all layers |
| `outline` | color, [thickness] | Outline non-zero pixels |
| `shade_band` | color, layer, side, [thickness] | Add shading |
| `noise_points` | color, layer, count, seed | Deterministic noise |
| `mirror` | [axis] | Mirror layer (x or y) |
| `translate` | dx, dy | Translate layer |
| `rotate` | angle, [cx, cy] | Rotate layer |

### Frame Inheritance

Frames can inherit from previous frames:

```json
{
  "base": 0,
  "overrides": [
    { "op_index": 5, "op": ["rect_fill", 2, 12, 10, 12, 12] }
  ],
  "append_ops": [
    ["pixel", 1, 15, 15]
  ]
}
```

## TUI Editor Controls

| Key | Action |
|-----|--------|
| ↑↓←→ | Move cursor |
| Space | Paint with current color |
| X | Erase (set to transparent) |
| C/Z | Next/Previous color |
| U/R | Undo/Redo |
| N/P | Next/Previous frame |
| A | Add new frame |
| D | Duplicate current frame |
| S | Save |
| Q | Quit |

## License

MIT

