<p align="center">
    <a href="https://github.com/bloomberg-sudo-dev/spriteforge">
        <img src="https://raw.githubusercontent.com/bloomberg-sudo-dev/spriteforge/main/logo/banner.png">
    </a>
</p>

[![pypi version](https://img.shields.io/pypi/v/spriteforge?logo=pypi)](https://pypi.org/project/spriteforge/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](http://choosealicense.com/licenses/mit/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Spriteforge is a deterministic, terminal-first pixel sprite compiler designed for creating game-ready spritesheets and animations from JSON definitions.

Note, Spriteforge is designed to be a **build tool**, not a runtime library. It compiles `.spriteops.json` files into spritesheets, animated GIFs, and metadata that can be used directly by game engines. The JSON format is simple enough for AI code assistants to generate, making it ideal for procedural sprite workflows.

## Installation

> [!Warning]
> Spriteforge is a CLI tool, not a library. If you're looking to embed sprite rendering in your Python code, you'll need to import from `spriteforge.engine` directly.

> [!Note]
> The package name is `spriteforge`. Install with `pip install spriteforge` or `pipx install spriteforge` for isolated global access.

Spriteforge runs on Python 3.8 or higher.

System requirements are [Pillow](https://pillow.readthedocs.io/) (installed automatically) and optionally [Textual](https://textual.textualize.io/) for the TUI editor.

### Directly

```sh
# Install spriteforge
pip install spriteforge

# Try it out
spriteforge new hello --w 16 --h 16
spriteforge edit hello.spriteops.json
```

For more options, take a look at the [Using Spriteforge](#using-spriteforge) section below.

If you want to hack on spriteforge itself, clone this repository and in that directory execute:

```sh
# Install spriteforge in development mode
pip install -e .

# Try it out
spriteforge new test_sprite
spriteforge render test_sprite.spriteops.json --outdir out --scale 4
```

### With pipx (Recommended)

```sh
# Install globally with pipx
pipx install spriteforge

# Create and edit a sprite
spriteforge new hero --w 32 --h 32 --palette pico8
spriteforge edit hero.spriteops.json
```

## Using Spriteforge

Try running the following:

```sh
spriteforge new my_sprite --w 32 --h 32 --palette pico8
spriteforge edit my_sprite.spriteops.json
```

This will create a new sprite file and open the TUI editor where you can paint pixels directly in your terminal.

Look through the [examples](./examples/) directory to see sample sprite definitions. The spriteops format supports:
- Multi-frame animations with inheritance
- Layer-based composition
- Raster primitives (lines, circles, polygons, bezier curves)
- Shading, outlines, and noise effects

When running in the CLI, the main commands are:

| Command | Description |
|---------|-------------|
| `spriteforge new <name>` | Create a new spriteops JSON file |
| `spriteforge edit <file>` | Open the TUI pixel editor |
| `spriteforge validate <file\|dir>` | Validate JSON structure and operations |
| `spriteforge render <file\|dir>` | Compile to spritesheet, GIF, and metadata |

### Render Options

```sh
spriteforge render my_sprite.spriteops.json --outdir dist --scale 4 --gif --frames
```

* `--outdir <dir>` (required) - Output directory for generated files
* `--scale N` - Scale factor for output images (default: 1)
* `--layout horizontal|grid` - Spritesheet layout (default: horizontal)
* `--cols N` - Columns for grid layout (default: 4)
* `--frames` - Export individual frame PNGs
* `--gif` - Export animated GIF

### Validation Options

```sh
spriteforge validate sprites/ --strict
```

* `--strict` - Enable strict mode (require seeds for noise, etc.)

Take a look at the [schema](./schemas/spriteops.schema.json) for the complete format specification.

## Spriteops Format

```json
{
  "format": "spriteops",
  "version": 1,
  "canvas": { "w": 32, "h": 32 },
  "palette": ["#00000000", "#1a1c2c", "#5d275d", "#b13e53", ...],
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

### Supported Operations

| Category | Operations |
|----------|------------|
| **Drawing** | `pixel`, `line`, `rect_fill`, `rect_stroke`, `ellipse_fill`, `circle_fill`, `poly_fill`, `fill`, `bezier` |
| **Layers** | `layer_begin`, `layer_end`, `layer_merge`, `ensure_layer`, `copy_layer`, `mask_layer` |
| **Effects** | `outline`, `shade_band`, `noise_points`, `gradient_radial`, `gradient_linear`, `color_replace`, `dither_rect` |
| **Transform** | `translate`, `rotate`, `mirror` |

### Frame Inheritance

Frames can inherit from previous frames for efficient animation:

```json
{
  "base": 0,
  "overrides": [{ "op_index": 5, "op": ["rect_fill", 2, 12, 10, 12, 12] }],
  "append_ops": [["pixel", 1, 15, 15]]
}
```

## TUI Editor

The built-in terminal editor provides a zoomed pixel canvas with keyboard controls:

| Key | Action |
|-----|--------|
| ↑↓←→ | Move cursor |
| Space | Paint with current color |
| X | Erase (set to transparent) |
| C/Z | Next/Previous palette color |
| U/R | Undo/Redo |
| N/P | Next/Previous frame |
| A | Add new frame |
| D | Duplicate current frame |
| Tab | Toggle animation preview |
| S | Save |
| Q | Quit |

## Contributing

Contributions are welcome! Please explain the motivation for a given change and include examples of its effect. Open an issue first for major changes.

## License

This project falls under the MIT license.
