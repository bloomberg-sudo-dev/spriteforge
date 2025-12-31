"""Operation definitions and specifications for Spriteforge."""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass


@dataclass
class OpSpec:
    """Specification for a spriteops operation."""
    name: str
    min_args: int
    max_args: int
    arg_types: List[str]  # 'int', 'str', 'float', 'color_idx', 'layer_name'
    description: str
    requires_layer: Optional[str] = None  # Name of layer reference argument position
    requires_seed: bool = False


# Complete operation specifications
# Parameter order is EXACTLY as in the original main.py - DO NOT CHANGE
OP_SPECS: Dict[str, OpSpec] = {
    # Basic operations
    "clear": OpSpec("clear", 1, 1, ["color_idx"], "Clear all layers to a color"),
    "pixel": OpSpec("pixel", 3, 3, ["color_idx", "int", "int"], "Set a single pixel"),
    
    # Layer operations
    "layer_begin": OpSpec("layer_begin", 1, 1, ["str"], "Begin a named layer"),
    "layer_end": OpSpec("layer_end", 0, 0, [], "End current layer"),
    "layer_merge": OpSpec("layer_merge", 0, 1, ["str"], "Merge all layers"),
    "copy_layer": OpSpec("copy_layer", 2, 2, ["str", "str"], "Copy layer src to dst"),
    
    # Shape primitives
    "line": OpSpec("line", 5, 5, ["color_idx", "int", "int", "int", "int"], "Draw a line"),
    "thick_line": OpSpec("thick_line", 6, 6, ["color_idx", "int", "int", "int", "int", "int"], "Draw a thick line"),
    "rect": OpSpec("rect", 5, 5, ["color_idx", "int", "int", "int", "int"], "Draw rectangle outline"),
    "rect_fill": OpSpec("rect_fill", 5, 5, ["color_idx", "int", "int", "int", "int"], "Draw filled rectangle"),
    "rect_stroke": OpSpec("rect_stroke", 5, 5, ["color_idx", "int", "int", "int", "int"], "Draw rectangle outline"),
    "ellipse_fill": OpSpec("ellipse_fill", 5, 5, ["color_idx", "int", "int", "int", "int"], "Draw filled ellipse"),
    "ellipse_stroke": OpSpec("ellipse_stroke", 5, 5, ["color_idx", "int", "int", "int", "int"], "Draw ellipse outline"),
    "circle_fill": OpSpec("circle_fill", 4, 4, ["color_idx", "int", "int", "int"], "Draw filled circle"),
    "capsule_fill": OpSpec("capsule_fill", 6, 6, ["color_idx", "int", "int", "int", "int", "int"], "Draw capsule shape"),
    "poly_fill": OpSpec("poly_fill", 3, 100, ["color_idx"], "Draw filled polygon (pairs of x,y follow)"),
    "bezier": OpSpec("bezier", 7, 7, ["color_idx", "int", "int", "int", "int", "int", "int"], "Draw quadratic bezier curve"),
    
    # Fill operations
    "fill": OpSpec("fill", 3, 3, ["color_idx", "int", "int"], "Flood fill from point"),
    "inset_fill": OpSpec("inset_fill", 6, 6, ["color_idx", "int", "int", "int", "int", "int"], "Fill with inset"),
    "dither_rect": OpSpec("dither_rect", 5, 6, ["color_idx", "int", "int", "int", "int", "str"], "Draw dithered rectangle"),
    
    # Gradient operations
    "gradient_radial": OpSpec("gradient_radial", 4, 4, ["str", "int", "int", "int"], "Draw radial gradient"),
    "gradient_linear": OpSpec("gradient_linear", 5, 5, ["str", "int", "int", "int", "int"], "Draw linear gradient"),
    
    # Layer effects
    "mask_layer": OpSpec("mask_layer", 1, 1, ["layer_name"], "Mask current layer by another", requires_layer="0"),
    "outline": OpSpec("outline", 1, 2, ["color_idx", "int"], "Add outline around all non-zero pixels"),
    "outline_layer": OpSpec("outline_layer", 1, 2, ["color_idx", "int"], "Add outline to current layer"),
    "shade_band": OpSpec("shade_band", 3, 4, ["color_idx", "layer_name", "str", "int"], "Add shading band", requires_layer="1"),
    "noise_points": OpSpec("noise_points", 4, 4, ["color_idx", "layer_name", "int", "int"], "Add noise points", requires_layer="1", requires_seed=True),
    "color_replace": OpSpec("color_replace", 2, 3, ["color_idx", "color_idx", "layer_name"], "Replace one color with another"),
    
    # Transform operations
    "translate": OpSpec("translate", 2, 2, ["int", "int"], "Translate current layer"),
    "rotate": OpSpec("rotate", 1, 3, ["float", "float", "float"], "Rotate current layer"),
    "mirror": OpSpec("mirror", 0, 1, ["str"], "Mirror current layer"),
}


def get_op_spec(name: str) -> Optional[OpSpec]:
    """Get the specification for an operation."""
    return OP_SPECS.get(name)


def get_all_op_names() -> List[str]:
    """Get all valid operation names."""
    return list(OP_SPECS.keys())

