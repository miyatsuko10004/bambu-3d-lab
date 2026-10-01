#!/usr/bin/env python3
"""Generate high-precision standalone ``瑛万 / emma`` text models.

The supplied PDF contains the Japanese brush glyphs as embedded Type 3 vector
paths. This generator extracts those paths directly instead of rasterizing the
PDF, then extrudes them into watertight polygon bodies. English text is rendered
at high resolution and unioned into polygon runs before extrusion.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import trimesh
from pypdf import PdfReader
from shapely.affinity import scale, translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parent.parent
PDF_SOURCE = ROOT / "assets" / "瑛万.pdf"
OUTPUT_REGULAR = ROOT / "models" / "eima_emma_text_only.stl"
OUTPUT_CURSIVE = ROOT / "models" / "eima_emma_text_only_cursive.stl"

NUMBER = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
TOKEN = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z]+")


def _cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )


def _parse_type3_path(data: bytes, curve_steps: int = 24):
    """Parse the subset of PDF path operators used by the embedded glyphs."""
    tokens = TOKEN.findall(data.decode("latin1"))
    numbers = []
    paths = []
    current = None
    start = None

    def pop(count):
        values = numbers[-count:]
        del numbers[-count:]
        return values

    for token in tokens:
        if NUMBER.fullmatch(token):
            numbers.append(float(token))
            continue
        if token == "d1":
            del numbers[-6:]
        elif token == "m":
            x, y = pop(2)
            current = [(x, y)]
            paths.append(current)
            start = (x, y)
        elif token == "l":
            current.append(tuple(pop(2)))
        elif token == "c":
            x1, y1, x2, y2, x3, y3 = pop(6)
            p0 = current[-1]
            current.extend(
                _cubic(p0, (x1, y1), (x2, y2), (x3, y3), i / curve_steps)
                for i in range(1, curve_steps + 1)
            )
        elif token == "y":
            x2, y2, x3, y3 = pop(4)
            p0 = current[-1]
            current.extend(
                _cubic(p0, p0, (x2, y2), (x3, y3), i / curve_steps)
                for i in range(1, curve_steps + 1)
            )
        elif token == "h":
            if current and current[-1] != start:
                current.append(start)

    return [path for path in paths if len(path) >= 4]


def _signed_area(points):
    return 0.5 * sum(
        points[i][0] * points[i + 1][1] - points[i + 1][0] * points[i][1]
        for i in range(len(points) - 1)
    )


def _normalise_geometry(geometry):
    """Flip PDF font Y-up coordinates and move geometry to local origin."""
    geometry = scale(geometry, xfact=1.0, yfact=-1.0, origin=(0, 0)).buffer(0)
    min_x, min_y, _, _ = geometry.bounds
    return translate(geometry, xoff=-min_x, yoff=-min_y)


def extract_pdf_glyph(pdf_path: Path, font_key: str, charproc_key: str):
    reader = PdfReader(str(pdf_path))
    page = reader.pages[0]
    font = page["/Resources"]["/Font"][font_key].get_object()
    charproc = font["/CharProcs"][charproc_key].get_object().get_data()
    paths = _parse_type3_path(charproc)
    rings = []
    for path in paths:
        polygon = Polygon(path).buffer(0)
        if not polygon.is_empty:
            rings.append((_signed_area(path), polygon))
    if not rings:
        raise ValueError(f"No vector contours found in {font_key} {charproc_key}")

    outer_sign = -1 if any(area < 0 for area, _ in rings) else 1
    filled = unary_union([polygon for area, polygon in rings if area * outer_sign > 0])
    holes = unary_union([polygon for area, polygon in rings if area * outer_sign < 0])
    return _normalise_geometry(filled.difference(holes))


def _read_pgm(data):
    stream = io.BytesIO(data)

    def token():
        value = bytearray()
        while True:
            char = stream.read(1)
            if not char:
                raise ValueError("Unexpected end of PGM header")
            if char == b"#":
                stream.readline()
                continue
            if char.isspace():
                if value:
                    return bytes(value)
                continue
            value.extend(char)

    if token() != b"P5":
        raise ValueError("Expected binary PGM")
    width, height, max_value = int(token()), int(token()), int(token())
    if max_value != 255:
        raise ValueError("Expected 8-bit PGM")
    pixels = stream.read(width * height)
    if len(pixels) != width * height:
        raise ValueError("Truncated PGM")
    return width, height, pixels


def render_mask(*, text, font, max_width_px=800, threshold=58):
    magick = shutil.which("magick") or shutil.which("convert")
    if not magick:
        raise RuntimeError("ImageMagick (magick or convert) is required")
    with tempfile.NamedTemporaryFile(suffix=".pgm") as tmp:
        args = [magick, "-background", "white", "-fill", "black", "-font", font,
                "-pointsize", "220", f"label:{text}", "-alpha", "off",
                "-colorspace", "Gray", "-threshold", f"{threshold}%",
                "-morphology", "Close", "Disk:1", "-trim", "+repage",
                "-resize", f"{max_width_px}x{max_width_px}", "-depth", "8",
                "PGM:" + tmp.name]
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return _read_pgm(Path(tmp.name).read_bytes())


def mask_to_geometry(mask):
    """Convert a high-resolution mask to a small set of unioned polygons."""
    width, height, pixels = mask
    runs = []
    for y in range(height):
        x = 0
        while x < width:
            if pixels[y * width + x] >= 128:
                x += 1
                continue
            start = x
            while x < width and pixels[y * width + x] < 128:
                x += 1
            runs.append(box(start, height - y - 1, x, height - y))
    if not runs:
        raise ValueError("Text mask is empty")
    geometry = _normalise_geometry(unary_union(runs))

    # Remove sub-pixel raster holes, while preserving real counters in letters.
    def clean(poly):
        holes = [ring for ring in poly.interiors if Polygon(ring).area >= 20.0]
        return Polygon(poly.exterior, holes)

    if geometry.geom_type == "Polygon":
        return clean(geometry).buffer(0)
    return unary_union([clean(poly) for poly in geometry.geoms]).buffer(0)


def place_geometry(geometry, *, x, y, width):
    current_width = geometry.bounds[2] - geometry.bounds[0]
    return translate(scale(geometry, xfact=width / current_width,
                           yfact=width / current_width, origin=(0, 0)), xoff=x, yoff=y)


def _polygons(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    return [part for part in geometry.geoms if part.geom_type == "Polygon"]


def write_mesh(geometries, path: Path, height=3.0):
    parts = [
        trimesh.creation.extrude_polygon(polygon, height, engine="manifold")
        for geometry in geometries
        for polygon in _polygons(geometry)
    ]
    mesh = trimesh.util.concatenate(parts)
    mesh.merge_vertices()
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(path)
    components = mesh.split(only_watertight=False)
    watertight_parts = sum(part.is_watertight for part in components)
    print(f"  -> {path} ({len(mesh.faces):,} triangles)")
    print(f"     bounds: {mesh.bounds[0].round(3)} .. {mesh.bounds[1].round(3)} mm")
    print(f"     solid_parts={len(components)}, watertight_parts={watertight_parts}/{len(components)}")


def generate(output=OUTPUT_REGULAR, english_font="/System/Library/Fonts/MarkerFelt.ttc",
             english_text="emma"):
    if not PDF_SOURCE.exists():
        raise FileNotFoundError(f"Missing PDF source: {PDF_SOURCE}")
    base_z = 0.0
    del base_z  # Geometry is already placed at Z=0 by extrude_polygon.

    # These are the two embedded brush glyphs used by the supplied PDF.
    eima = extract_pdf_glyph(PDF_SOURCE, "/F18", "/g396")
    man = extract_pdf_glyph(PDF_SOURCE, "/F19", "/g8D6")
    japanese = [
        place_geometry(eima, x=16.0, y=38.0, width=24.0),
        place_geometry(man, x=16.0, y=10.0, width=24.0),
    ]

    english_mask = render_mask(text=english_text, font=english_font, max_width_px=800)
    english = place_geometry(mask_to_geometry(english_mask), x=52.0, y=22.0, width=62.0)
    write_mesh(japanese + [english], output)


if __name__ == "__main__":
    print("瑛万 / emma の高精度通常版を生成中...")
    generate()
    print("瑛万 / Emma の高精度筆記体版を生成中...")
    generate(OUTPUT_CURSIVE, "/System/Library/Fonts/Supplemental/Brush Script.ttf", "Emma")
    print("印刷想定: 文字のみ・厚み3.0mm, 単色PLA, サポートなし")
