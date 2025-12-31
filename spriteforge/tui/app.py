"""Spriteforge TUI application using Textual."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive
from textual import events

from ..engine.raster import hex_to_rgba
from ..engine.render import render_frame


class PixelCanvas(Static):
    """A widget that displays and allows editing of a pixel canvas."""
    
    cursor_x = reactive(0)
    cursor_y = reactive(0)
    current_color = reactive(1)
    zoom = reactive(8)
    
    def __init__(self, width: int, height: int, palette: List[str], **kwargs):
        super().__init__(**kwargs)
        self.canvas_width = width
        self.canvas_height = height
        self.palette = palette
        self.palette_rgba = [hex_to_rgba(c) for c in palette]
        self.buffer: List[int] = [0] * (width * height)
        self.undo_stack: List[List[int]] = []
        self.redo_stack: List[List[int]] = []
    
    def compose(self) -> ComposeResult:
        yield Static("", id="canvas-display")
    
    def on_mount(self) -> None:
        self.refresh_display()
    
    def refresh_display(self) -> None:
        """Refresh the canvas display."""
        lines = []
        for y in range(self.canvas_height):
            row = ""
            for x in range(self.canvas_width):
                idx = self.buffer[y * self.canvas_width + x]
                if x == self.cursor_x and y == self.cursor_y:
                    row += "█"  # Cursor
                elif idx == 0:
                    row += "·"  # Transparent
                else:
                    # Use block character with color hint
                    row += "▓"
            lines.append(row)
        
        display = self.query_one("#canvas-display", Static)
        display.update("\n".join(lines))
    
    def watch_cursor_x(self, value: int) -> None:
        self.cursor_x = max(0, min(value, self.canvas_width - 1))
        self.refresh_display()
    
    def watch_cursor_y(self, value: int) -> None:
        self.cursor_y = max(0, min(value, self.canvas_height - 1))
        self.refresh_display()
    
    def push_undo(self) -> None:
        """Save current state to undo stack."""
        self.undo_stack.append(self.buffer[:])
        self.redo_stack.clear()
        # Limit undo history
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
    
    def undo(self) -> None:
        """Undo last change."""
        if self.undo_stack:
            self.redo_stack.append(self.buffer[:])
            self.buffer = self.undo_stack.pop()
            self.refresh_display()
    
    def redo(self) -> None:
        """Redo last undone change."""
        if self.redo_stack:
            self.undo_stack.append(self.buffer[:])
            self.buffer = self.redo_stack.pop()
            self.refresh_display()
    
    def paint(self) -> None:
        """Paint at cursor position with current color."""
        self.push_undo()
        self.buffer[self.cursor_y * self.canvas_width + self.cursor_x] = self.current_color
        self.refresh_display()
    
    def erase(self) -> None:
        """Erase at cursor position (set to transparent)."""
        self.push_undo()
        self.buffer[self.cursor_y * self.canvas_width + self.cursor_x] = 0
        self.refresh_display()
    
    def load_from_ops(self, ops: List[List[Any]]) -> None:
        """Load buffer from operations."""
        self.buffer = render_frame(ops, self.canvas_width, self.canvas_height)
        self.refresh_display()
    
    def to_ops(self) -> List[List[Any]]:
        """Convert buffer to compact operations."""
        ops: List[List[Any]] = [["clear", 0]]
        
        # Find runs and use rect_fill where possible
        # For simplicity, just emit pixel ops for non-zero pixels
        for y in range(self.canvas_height):
            x = 0
            while x < self.canvas_width:
                idx = self.buffer[y * self.canvas_width + x]
                if idx != 0:
                    # Check for horizontal run
                    run_end = x + 1
                    while run_end < self.canvas_width and self.buffer[y * self.canvas_width + run_end] == idx:
                        run_end += 1
                    
                    run_len = run_end - x
                    if run_len >= 3:
                        # Use rect_fill for runs of 3+
                        ops.append(["rect_fill", idx, x, y, run_len, 1])
                    else:
                        # Use individual pixels
                        for px in range(x, run_end):
                            ops.append(["pixel", idx, px, y])
                    x = run_end
                else:
                    x += 1
        
        return ops


class PaletteSelector(Static):
    """Widget for selecting colors from the palette."""
    
    selected_index = reactive(1)
    
    def __init__(self, palette: List[str], **kwargs):
        super().__init__(**kwargs)
        self.palette = palette
    
    def compose(self) -> ComposeResult:
        yield Static("", id="palette-display")
    
    def on_mount(self) -> None:
        self.refresh_display()
    
    def refresh_display(self) -> None:
        """Refresh palette display."""
        items = []
        for i, color in enumerate(self.palette):
            marker = "→" if i == self.selected_index else " "
            if i == 0:
                items.append(f"{marker} {i}: [transparent]")
            else:
                items.append(f"{marker} {i}: {color}")
        
        display = self.query_one("#palette-display", Static)
        display.update("\n".join(items))
    
    def watch_selected_index(self, value: int) -> None:
        self.selected_index = max(0, min(value, len(self.palette) - 1))
        self.refresh_display()
    
    def next_color(self) -> None:
        """Select next color."""
        self.selected_index = (self.selected_index + 1) % len(self.palette)
    
    def prev_color(self) -> None:
        """Select previous color."""
        self.selected_index = (self.selected_index - 1) % len(self.palette)


class FrameList(Static):
    """Widget for listing and managing frames."""
    
    selected_frame = reactive(0)
    
    def __init__(self, frame_count: int, **kwargs):
        super().__init__(**kwargs)
        self.frame_count = frame_count
    
    def compose(self) -> ComposeResult:
        yield Static("", id="frame-list-display")
    
    def on_mount(self) -> None:
        self.refresh_display()
    
    def refresh_display(self) -> None:
        """Refresh frame list display."""
        items = []
        for i in range(self.frame_count):
            marker = "→" if i == self.selected_frame else " "
            items.append(f"{marker} Frame {i}")
        
        display = self.query_one("#frame-list-display", Static)
        display.update("\n".join(items))
    
    def watch_selected_frame(self, value: int) -> None:
        self.selected_frame = max(0, min(value, self.frame_count - 1))
        self.refresh_display()


class SpritforgeApp(App):
    """Spriteforge TUI editor application."""
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 2fr 1fr;
    }
    
    #left-panel {
        height: 100%;
        border: solid green;
    }
    
    #canvas-panel {
        height: 100%;
        border: solid blue;
    }
    
    #right-panel {
        height: 100%;
        border: solid yellow;
    }
    
    .panel-title {
        text-style: bold;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save", "Save"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
        Binding("left", "cursor_left", "Left"),
        Binding("right", "cursor_right", "Right"),
        Binding("space", "paint", "Paint"),
        Binding("x", "erase", "Erase"),
        Binding("c", "next_color", "Next Color"),
        Binding("z", "prev_color", "Prev Color"),
        Binding("u", "undo", "Undo"),
        Binding("r", "redo", "Redo"),
        Binding("n", "next_frame", "Next Frame"),
        Binding("p", "prev_frame", "Prev Frame"),
        Binding("a", "add_frame", "Add Frame"),
        Binding("d", "duplicate_frame", "Duplicate Frame"),
    ]
    
    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.data: Dict[str, Any] = {}
        self.current_frame_idx = 0
        self.modified = False
        
        # Load the file
        with open(file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        self.canvas_width = self.data["canvas"]["w"]
        self.canvas_height = self.data["canvas"]["h"]
        self.palette = self.data["palette"]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="left-panel"):
            yield Static("Palette", classes="panel-title")
            yield PaletteSelector(self.palette, id="palette")
            yield Static("", id="spacer")
            yield Static("Frames", classes="panel-title")
            yield FrameList(len(self.data["frames"]), id="frames")
        
        with Container(id="canvas-panel"):
            yield Static(f"Canvas ({self.canvas_width}x{self.canvas_height})", classes="panel-title")
            yield PixelCanvas(self.canvas_width, self.canvas_height, self.palette, id="canvas")
        
        with Container(id="right-panel"):
            yield Static("Info", classes="panel-title")
            yield Static("", id="info-display")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Load first frame on mount."""
        self.load_frame(0)
        self.update_info()
    
    def load_frame(self, idx: int) -> None:
        """Load a frame into the canvas."""
        if 0 <= idx < len(self.data["frames"]):
            self.current_frame_idx = idx
            frame = self.data["frames"][idx]
            ops = frame.get("ops", [])
            canvas = self.query_one("#canvas", PixelCanvas)
            canvas.load_from_ops(ops)
            
            frame_list = self.query_one("#frames", FrameList)
            frame_list.selected_frame = idx
    
    def save_frame(self) -> None:
        """Save current canvas to current frame."""
        canvas = self.query_one("#canvas", PixelCanvas)
        ops = canvas.to_ops()
        self.data["frames"][self.current_frame_idx]["ops"] = ops
        self.modified = True
    
    def update_info(self) -> None:
        """Update info panel."""
        canvas = self.query_one("#canvas", PixelCanvas)
        palette = self.query_one("#palette", PaletteSelector)
        
        info_lines = [
            f"File: {self.file_path.name}",
            f"Frame: {self.current_frame_idx + 1}/{len(self.data['frames'])}",
            f"Cursor: ({canvas.cursor_x}, {canvas.cursor_y})",
            f"Color: {palette.selected_index}",
            f"Modified: {'Yes' if self.modified else 'No'}",
            "",
            "Controls:",
            "↑↓←→  Move cursor",
            "Space  Paint",
            "X      Erase",
            "C/Z    Next/Prev color",
            "U/R    Undo/Redo",
            "N/P    Next/Prev frame",
            "A      Add frame",
            "D      Duplicate frame",
            "S      Save",
            "Q      Quit",
        ]
        
        info = self.query_one("#info-display", Static)
        info.update("\n".join(info_lines))
    
    # Actions
    def action_cursor_up(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.cursor_y -= 1
        self.update_info()
    
    def action_cursor_down(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.cursor_y += 1
        self.update_info()
    
    def action_cursor_left(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.cursor_x -= 1
        self.update_info()
    
    def action_cursor_right(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.cursor_x += 1
        self.update_info()
    
    def action_paint(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        palette = self.query_one("#palette", PaletteSelector)
        canvas.current_color = palette.selected_index
        canvas.paint()
        self.modified = True
        self.update_info()
    
    def action_erase(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.erase()
        self.modified = True
        self.update_info()
    
    def action_next_color(self) -> None:
        palette = self.query_one("#palette", PaletteSelector)
        palette.next_color()
        self.update_info()
    
    def action_prev_color(self) -> None:
        palette = self.query_one("#palette", PaletteSelector)
        palette.prev_color()
        self.update_info()
    
    def action_undo(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.undo()
        self.update_info()
    
    def action_redo(self) -> None:
        canvas = self.query_one("#canvas", PixelCanvas)
        canvas.redo()
        self.update_info()
    
    def action_next_frame(self) -> None:
        self.save_frame()
        if self.current_frame_idx < len(self.data["frames"]) - 1:
            self.load_frame(self.current_frame_idx + 1)
        self.update_info()
    
    def action_prev_frame(self) -> None:
        self.save_frame()
        if self.current_frame_idx > 0:
            self.load_frame(self.current_frame_idx - 1)
        self.update_info()
    
    def action_add_frame(self) -> None:
        self.save_frame()
        new_frame = {
            "durationMs": 100,
            "ops": [["clear", 0]]
        }
        self.data["frames"].append(new_frame)
        
        frame_list = self.query_one("#frames", FrameList)
        frame_list.frame_count = len(self.data["frames"])
        frame_list.refresh_display()
        
        self.load_frame(len(self.data["frames"]) - 1)
        self.modified = True
        self.update_info()
    
    def action_duplicate_frame(self) -> None:
        self.save_frame()
        current_frame = self.data["frames"][self.current_frame_idx]
        new_frame = {
            "durationMs": current_frame.get("durationMs", 100),
            "ops": list(current_frame.get("ops", []))
        }
        self.data["frames"].insert(self.current_frame_idx + 1, new_frame)
        
        frame_list = self.query_one("#frames", FrameList)
        frame_list.frame_count = len(self.data["frames"])
        frame_list.refresh_display()
        
        self.load_frame(self.current_frame_idx + 1)
        self.modified = True
        self.update_info()
    
    def action_save(self) -> None:
        self.save_frame()
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        self.modified = False
        self.notify(f"Saved to {self.file_path}")
        self.update_info()
    
    def action_quit(self) -> None:
        if self.modified:
            self.notify("Unsaved changes! Press S to save or Q again to quit without saving.")
            self.modified = False  # Allow quit on second press
        else:
            self.exit()

