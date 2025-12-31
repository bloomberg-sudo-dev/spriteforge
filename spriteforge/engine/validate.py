"""Validation for Spriteforge spriteops JSON files."""

import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .ops import OP_SPECS, get_op_spec


class ValidationError(Exception):
    """Raised when validation fails."""
    
    def __init__(self, message: str, path: Optional[str] = None, frame: Optional[int] = None, op_index: Optional[int] = None):
        self.message = message
        self.path = path
        self.frame = frame
        self.op_index = op_index
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format the error message with context."""
        parts = []
        if self.path:
            parts.append(f"File: {self.path}")
        if self.frame is not None:
            parts.append(f"Frame: {self.frame}")
        if self.op_index is not None:
            parts.append(f"Op #{self.op_index}")
        
        location = " | ".join(parts)
        if location:
            return f"{location}\n  Error: {self.message}"
        return self.message


def validate_sprite(data: Dict[str, Any], path: Optional[str] = None, strict: bool = False) -> List[ValidationError]:
    """
    Validate a spriteops JSON structure.
    
    Returns a list of validation errors. Empty list means valid.
    """
    errors: List[ValidationError] = []
    
    # Check required top-level fields
    if data.get("format") != "spriteops":
        errors.append(ValidationError("Missing or invalid 'format' field (expected 'spriteops')", path))
    
    if "canvas" not in data:
        errors.append(ValidationError("Missing 'canvas' field", path))
    else:
        canvas = data["canvas"]
        if "w" not in canvas or "h" not in canvas:
            errors.append(ValidationError("Canvas must have 'w' and 'h' fields", path))
        elif not isinstance(canvas["w"], int) or not isinstance(canvas["h"], int):
            errors.append(ValidationError("Canvas 'w' and 'h' must be integers", path))
        elif canvas["w"] <= 0 or canvas["h"] <= 0:
            errors.append(ValidationError("Canvas dimensions must be positive", path))
    
    # Check palette
    if "palette" not in data:
        errors.append(ValidationError("Missing 'palette' field", path))
    elif not isinstance(data["palette"], list):
        errors.append(ValidationError("'palette' must be an array", path))
    elif len(data["palette"]) == 0:
        errors.append(ValidationError("'palette' cannot be empty", path))
    else:
        palette_size = len(data["palette"])
        for i, color in enumerate(data["palette"]):
            if not isinstance(color, str):
                errors.append(ValidationError(f"Palette color {i} must be a hex string", path))
            elif not color.startswith("#"):
                errors.append(ValidationError(f"Palette color {i} must start with '#'", path))
    
    # Check frames
    if "frames" not in data:
        errors.append(ValidationError("Missing 'frames' field", path))
    elif not isinstance(data["frames"], list):
        errors.append(ValidationError("'frames' must be an array", path))
    elif len(data["frames"]) == 0:
        errors.append(ValidationError("'frames' cannot be empty", path))
    else:
        palette_size = len(data.get("palette", []))
        for frame_idx, frame in enumerate(data["frames"]):
            frame_errors = validate_frame(frame, frame_idx, palette_size, path, strict)
            errors.extend(frame_errors)
    
    # Check animations if present
    if "animations" in data:
        frame_count = len(data.get("frames", []))
        for anim_name, anim_data in data["animations"].items():
            if "frames" in anim_data:
                for f in anim_data["frames"]:
                    if not isinstance(f, int) or f < 0 or f >= frame_count:
                        errors.append(ValidationError(
                            f"Animation '{anim_name}' references invalid frame index: {f}",
                            path
                        ))
    
    return errors


def validate_frame(frame: Dict[str, Any], frame_idx: int, palette_size: int, path: Optional[str], strict: bool) -> List[ValidationError]:
    """Validate a single frame."""
    errors: List[ValidationError] = []
    
    # Frame inheritance
    if "base" in frame:
        if not isinstance(frame["base"], int):
            errors.append(ValidationError("Frame 'base' must be an integer", path, frame_idx))
        elif frame["base"] >= frame_idx:
            errors.append(ValidationError(f"Frame 'base' must reference an earlier frame (got {frame['base']})", path, frame_idx))
        # If using inheritance, ops is optional
        if "ops" not in frame and "overrides" not in frame and "append_ops" not in frame:
            errors.append(ValidationError("Inherited frame must have 'overrides' or 'append_ops'", path, frame_idx))
    else:
        if "ops" not in frame:
            errors.append(ValidationError("Frame must have 'ops' array", path, frame_idx))
        elif not isinstance(frame["ops"], list):
            errors.append(ValidationError("Frame 'ops' must be an array", path, frame_idx))
        else:
            # Track defined layers for reference checking
            defined_layers = {"base"}
            
            for op_idx, op in enumerate(frame["ops"]):
                op_errors = validate_op(op, op_idx, palette_size, defined_layers, path, frame_idx, strict)
                errors.extend(op_errors)
                
                # Track layer definitions
                if isinstance(op, list) and len(op) >= 2 and op[0] == "layer_begin":
                    defined_layers.add(str(op[1]))
    
    return errors


def validate_op(op: Any, op_idx: int, palette_size: int, defined_layers: set, path: Optional[str], frame_idx: int, strict: bool) -> List[ValidationError]:
    """Validate a single operation."""
    errors: List[ValidationError] = []
    
    if not isinstance(op, list):
        errors.append(ValidationError("Operation must be an array", path, frame_idx, op_idx))
        return errors
    
    if len(op) == 0:
        errors.append(ValidationError("Operation cannot be empty", path, frame_idx, op_idx))
        return errors
    
    op_name = op[0]
    if not isinstance(op_name, str):
        errors.append(ValidationError("Operation name must be a string", path, frame_idx, op_idx))
        return errors
    
    spec = get_op_spec(op_name)
    if spec is None:
        errors.append(ValidationError(f"Unknown operation: '{op_name}'", path, frame_idx, op_idx))
        return errors
    
    # Check argument count (args are op[1:])
    arg_count = len(op) - 1
    if arg_count < spec.min_args:
        errors.append(ValidationError(
            f"Operation '{op_name}' requires at least {spec.min_args} arguments, got {arg_count}",
            path, frame_idx, op_idx
        ))
    elif arg_count > spec.max_args:
        errors.append(ValidationError(
            f"Operation '{op_name}' accepts at most {spec.max_args} arguments, got {arg_count}",
            path, frame_idx, op_idx
        ))
    
    # Check palette index bounds
    for i, arg in enumerate(op[1:]):
        if i < len(spec.arg_types):
            arg_type = spec.arg_types[i]
            if arg_type == "color_idx":
                if isinstance(arg, int):
                    if arg < 0 or arg >= palette_size:
                        errors.append(ValidationError(
                            f"Palette index {arg} out of bounds (palette has {palette_size} colors)",
                            path, frame_idx, op_idx
                        ))
    
    # Check layer references
    if spec.requires_layer:
        layer_arg_idx = int(spec.requires_layer)
        if layer_arg_idx + 1 < len(op):
            layer_name = str(op[layer_arg_idx + 1])
            if layer_name not in defined_layers:
                errors.append(ValidationError(
                    f"Operation '{op_name}' references undefined layer: '{layer_name}'",
                    path, frame_idx, op_idx
                ))
    
    # Check seed requirement for noise_points (determinism enforcement)
    if spec.requires_seed and strict:
        if op_name == "noise_points" and len(op) < 5:
            errors.append(ValidationError(
                "Operation 'noise_points' requires a seed for deterministic output",
                path, frame_idx, op_idx
            ))
    
    return errors


def validate_file(file_path: Path, strict: bool = False) -> Tuple[bool, List[ValidationError]]:
    """
    Validate a spriteops JSON file.
    
    Returns (is_valid, errors).
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [ValidationError(f"Invalid JSON: {e}", str(file_path))]
    except FileNotFoundError:
        return False, [ValidationError(f"File not found", str(file_path))]
    except Exception as e:
        return False, [ValidationError(f"Failed to read file: {e}", str(file_path))]
    
    errors = validate_sprite(data, str(file_path), strict)
    return len(errors) == 0, errors

