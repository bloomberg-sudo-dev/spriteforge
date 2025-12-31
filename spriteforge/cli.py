"""Command-line interface for Spriteforge."""

import sys
import json
from pathlib import Path
from typing import Optional, List

import click

from .engine.validate import validate_file, ValidationError
from .engine.render import render_sprite
from .engine.raster import hex_to_rgba


# Default palettes for new sprites
PALETTES = {
    "gameboy": ["#00000000", "#0f380f", "#306230", "#8bac0f", "#9bbc0f"],
    "pico8": [
        "#00000000", "#1d2b53", "#7e2553", "#008751",
        "#ab5236", "#5f574f", "#c2c3c7", "#fff1e8",
        "#ff004d", "#ffa300", "#ffec27", "#00e436",
        "#29adff", "#83769c", "#ff77a8", "#ffccaa"
    ],
    "grayscale": ["#00000000", "#000000", "#555555", "#aaaaaa", "#ffffff"],
    "default": [
        "#00000000", "#000000", "#ffffff", "#ff0000",
        "#00ff00", "#0000ff", "#ffff00", "#ff00ff"
    ]
}


@click.group()
@click.version_option(version="1.0.0", prog_name="spriteforge")
def main():
    """Spriteforge - A deterministic, terminal-first pixel sprite compiler."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Enable strict validation mode")
def validate(path: str, strict: bool):
    """Validate spriteops JSON files.
    
    PATH can be a single file or a directory containing .spriteops.json files.
    """
    path_obj = Path(path)
    
    if path_obj.is_file():
        files = [path_obj]
    else:
        files = list(path_obj.glob("**/*.spriteops.json"))
        if not files:
            click.echo(f"No .spriteops.json files found in {path}", err=True)
            sys.exit(1)
    
    total_errors = 0
    for file_path in files:
        is_valid, errors = validate_file(file_path, strict)
        
        if is_valid:
            click.echo(click.style(f"[OK] {file_path}", fg="green"))
        else:
            click.echo(click.style(f"[FAIL] {file_path}", fg="red"))
            for error in errors:
                click.echo(f"  {error.message}", err=True)
            total_errors += len(errors)
    
    if total_errors > 0:
        click.echo(f"\n{total_errors} error(s) found", err=True)
        sys.exit(1)
    else:
        click.echo(f"\n{len(files)} file(s) validated successfully")
        sys.exit(0)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--outdir", "-o", type=click.Path(), required=True, help="Output directory")
@click.option("--scale", "-s", type=int, default=1, help="Scale factor for output images")
@click.option("--layout", type=click.Choice(["horizontal", "grid"]), default="horizontal", help="Sprite sheet layout")
@click.option("--cols", type=int, default=4, help="Columns for grid layout")
@click.option("--frames", is_flag=True, help="Export individual frames")
@click.option("--gif", is_flag=True, help="Export animated GIF for multi-frame sprites")
def render(path: str, outdir: str, scale: int, layout: str, cols: int, frames: bool, gif: bool):
    """Render spriteops JSON files to images.
    
    PATH can be a single file or a directory containing .spriteops.json files.
    """
    path_obj = Path(path)
    outdir_obj = Path(outdir)
    
    # Create output directory if it doesn't exist
    outdir_obj.mkdir(parents=True, exist_ok=True)
    
    if path_obj.is_file():
        files = [path_obj]
    else:
        files = list(path_obj.glob("**/*.spriteops.json"))
        if not files:
            click.echo(f"No .spriteops.json files found in {path}", err=True)
            sys.exit(1)
    
    for file_path in files:
        # Validate first
        is_valid, errors = validate_file(file_path)
        if not is_valid:
            click.echo(click.style(f"[FAIL] {file_path} - validation failed", fg="red"), err=True)
            for error in errors:
                click.echo(f"  {error.message}", err=True)
            sys.exit(1)
        
        # Load and render
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract base name
            base_name = file_path.stem
            if base_name.endswith(".spriteops"):
                base_name = base_name[:-10]
            data["name"] = base_name
            
            meta = render_sprite(
                data,
                outdir_obj,
                scale=scale,
                layout=layout,
                cols=cols,
                export_frames=frames,
                export_gif=gif
            )
            
            click.echo(click.style(f"[OK] {file_path}", fg="green"))
            click.echo(f"  -> {outdir_obj / f'{base_name}_sheet.png'}")
            click.echo(f"  -> {outdir_obj / f'{base_name}_meta.json'}")
            if gif and meta["totalFrames"] > 1:
                click.echo(f"  -> {outdir_obj / f'{base_name}.gif'}")
            
        except Exception as e:
            click.echo(click.style(f"[FAIL] {file_path} - render failed: {e}", fg="red"), err=True)
            sys.exit(1)
    
    click.echo(f"\n{len(files)} sprite(s) rendered successfully")


@main.command()
@click.argument("name")
@click.option("--w", "-w", type=int, default=32, help="Canvas width")
@click.option("--h", "-h", "height", type=int, default=32, help="Canvas height")
@click.option("--palette", "-p", type=str, default="default", help="Palette preset or comma-separated hex colors")
def new(name: str, w: int, height: int, palette: str):
    """Create a new spriteops JSON file.
    
    NAME is the sprite name (will create NAME.spriteops.json).
    """
    # Determine palette
    if palette in PALETTES:
        colors = PALETTES[palette]
    elif "," in palette:
        colors = ["#00000000"] + [c.strip() for c in palette.split(",")]
    else:
        colors = PALETTES["default"]
    
    # Create template
    template = {
        "format": "spriteops",
        "version": 1,
        "canvas": {"w": w, "h": height},
        "palette": colors,
        "animations": {
            "idle": {"loop": True, "frames": [0]}
        },
        "frames": [
            {
                "durationMs": 100,
                "ops": [
                    ["clear", 0],
                    ["layer_begin", "main"],
                    ["layer_end"],
                    ["layer_merge", "final"],
                    ["outline", 1, 1]
                ]
            }
        ]
    }
    
    output_path = Path(f"{name}.spriteops.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    
    click.echo(click.style(f"[OK] Created {output_path}", fg="green"))
    click.echo(f"  Canvas: {w}x{height}")
    click.echo(f"  Palette: {palette} ({len(colors)} colors)")


@main.command()
@click.argument("path", type=click.Path(exists=True))
def edit(path: str):
    """Launch the TUI editor for a spriteops file.
    
    PATH must be a .spriteops.json file.
    """
    from .tui.app import SpritforgeApp
    
    path_obj = Path(path)
    if not path_obj.exists():
        click.echo(f"File not found: {path}", err=True)
        sys.exit(1)
    
    app = SpritforgeApp(path_obj)
    app.run()


if __name__ == "__main__":
    main()

