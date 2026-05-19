from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int
    job: dict


@dataclass
class PackResult:
    placed: List[Rect]
    unplaced: List[dict]
    mode_used: str
    notes: List[str]


def estimate_grid_capacity(
    usable_width_px: int,
    usable_height_px: int,
    item_width_px: int,
    item_height_px: int,
    gap_px: int,
) -> Tuple[int, int, int]:
    cols = math.floor((usable_width_px + gap_px) / (item_width_px + gap_px))
    rows = math.floor((usable_height_px + gap_px) / (item_height_px + gap_px))
    cols = max(cols, 0)
    rows = max(rows, 0)
    return cols, rows, cols * rows


def detect_unique_sizes(jobs: List[dict]) -> List[Tuple[int, int]]:
    return sorted({
        (job["width_px"], job["height_px"])
        for job in jobs
    })


def choose_packing_mode(jobs: List[dict], requested_mode: str = "auto") -> str:
    requested_mode = (requested_mode or "auto").strip().lower()

    if requested_mode != "auto":
        return requested_mode

    unique_sizes = detect_unique_sizes(jobs)

    if len(unique_sizes) == 1:
        return "grid"

    # Canonical divisible sizes: 25, 50, 100, 120, 150 mm usually convert
    # into clean relative pixel sizes when generated at the same DPI.
    # Guillotine keeps rows/blocks easier to cut.
    if len(unique_sizes) <= 5:
        return "guillotine"

    return "maxrects"


def pack_grid(
    jobs: List[dict],
    usable_width_px: int,
    usable_height_px: int,
    margin_px: int,
    gap_px: int,
) -> PackResult:
    notes = []

    if not jobs:
        return PackResult([], [], "grid", ["No jobs to pack."])

    unique_sizes = detect_unique_sizes(jobs)

    if len(unique_sizes) != 1:
        notes.append("Grid packing requested, but jobs contain mixed sizes. Falling back to shelf packing.")
        return pack_shelf(jobs, usable_width_px, usable_height_px, margin_px, gap_px)

    item_width_px, item_height_px = unique_sizes[0]
    cols, rows, capacity = estimate_grid_capacity(
        usable_width_px,
        usable_height_px,
        item_width_px,
        item_height_px,
        gap_px,
    )

    placed = []
    unplaced = []

    for index, job in enumerate(jobs):
        if index >= capacity:
            unplaced.append(job)
            continue

        row = index // cols
        col = index % cols

        x = margin_px + col * (item_width_px + gap_px)
        y = margin_px + row * (item_height_px + gap_px)

        placed.append(Rect(x, y, item_width_px, item_height_px, job))

    notes.append(f"Grid: {cols} columns × {rows} rows = {capacity} capacity")

    return PackResult(placed, unplaced, "grid", notes)


def pack_shelf(
    jobs: List[dict],
    usable_width_px: int,
    usable_height_px: int,
    margin_px: int,
    gap_px: int,
) -> PackResult:
    placed = []
    unplaced = []
    notes = []

    x = margin_px
    y = margin_px
    row_height = 0

    right = margin_px + usable_width_px
    bottom = margin_px + usable_height_px

    # Larger items first gives cleaner rows.
    sorted_jobs = sorted(
        jobs,
        key=lambda j: (j["height_px"], j["width_px"], j["height_px"] * j["width_px"]),
        reverse=True,
    )

    for job in sorted_jobs:
        w = job["width_px"]
        h = job["height_px"]

        if x + w > right:
            x = margin_px
            y += row_height + gap_px
            row_height = 0

        if y + h > bottom:
            unplaced.append(job)
            continue

        placed.append(Rect(x, y, w, h, job))

        x += w + gap_px
        row_height = max(row_height, h)

    notes.append("Shelf packing: predictable row-based layout.")

    return PackResult(placed, unplaced, "shelf", notes)


def pack_guillotine(
    jobs: List[dict],
    usable_width_px: int,
    usable_height_px: int,
    margin_px: int,
    gap_px: int,
) -> PackResult:
    """
    Simple guillotine-style free-rectangle packing.

    This favors cut-friendly block layouts more than maximum density.
    It places larger rectangles first, then splits remaining free space
    into right and bottom rectangles.
    """
    placed = []
    unplaced = []
    notes = []

    free_rects = [{
        "x": margin_px,
        "y": margin_px,
        "width": usable_width_px,
        "height": usable_height_px,
    }]

    sorted_jobs = sorted(
        jobs,
        key=lambda j: (j["height_px"] * j["width_px"], max(j["width_px"], j["height_px"])),
        reverse=True,
    )

    for job in sorted_jobs:
        w = job["width_px"]
        h = job["height_px"]

        best_index = None
        best_score = None

        for i, free in enumerate(free_rects):
            if w <= free["width"] and h <= free["height"]:
                leftover_w = free["width"] - w
                leftover_h = free["height"] - h
                score = min(leftover_w, leftover_h)

                if best_score is None or score < best_score:
                    best_score = score
                    best_index = i

        if best_index is None:
            unplaced.append(job)
            continue

        free = free_rects.pop(best_index)

        x = free["x"]
        y = free["y"]

        placed.append(Rect(x, y, w, h, job))

        remaining_right_width = free["width"] - w - gap_px
        remaining_bottom_height = free["height"] - h - gap_px

        # Split direction: preserve the larger leftover area.
        right_rect = {
            "x": x + w + gap_px,
            "y": y,
            "width": remaining_right_width,
            "height": h,
        }

        bottom_rect = {
            "x": x,
            "y": y + h + gap_px,
            "width": free["width"],
            "height": remaining_bottom_height,
        }

        if right_rect["width"] > 0 and right_rect["height"] > 0:
            free_rects.append(right_rect)

        if bottom_rect["width"] > 0 and bottom_rect["height"] > 0:
            free_rects.append(bottom_rect)

        # Keep free rectangles ordered top-to-bottom, then left-to-right.
        free_rects.sort(key=lambda r: (r["y"], r["x"], r["height"] * r["width"]))

    notes.append("Guillotine packing: cut-friendly free-rectangle layout.")

    return PackResult(placed, unplaced, "guillotine", notes)


def _maxrects_prune_free_rects(free_rects: List[dict]) -> List[dict]:
    pruned = []

    for i, rect in enumerate(free_rects):
        contained = False

        for j, other in enumerate(free_rects):
            if i == j:
                continue

            if (
                rect["x"] >= other["x"]
                and rect["y"] >= other["y"]
                and rect["x"] + rect["width"] <= other["x"] + other["width"]
                and rect["y"] + rect["height"] <= other["y"] + other["height"]
            ):
                contained = True
                break

        if not contained:
            pruned.append(rect)

    return pruned


def pack_maxrects(
    jobs: List[dict],
    usable_width_px: int,
    usable_height_px: int,
    margin_px: int,
    gap_px: int,
) -> PackResult:
    """
    Basic MaxRects-style packing.

    This is better for mixed sizes, but may create less cut-friendly layouts
    than guillotine packing.
    """
    placed = []
    unplaced = []
    notes = []

    free_rects = [{
        "x": margin_px,
        "y": margin_px,
        "width": usable_width_px,
        "height": usable_height_px,
    }]

    sorted_jobs = sorted(
        jobs,
        key=lambda j: j["height_px"] * j["width_px"],
        reverse=True,
    )

    for job in sorted_jobs:
        w = job["width_px"]
        h = job["height_px"]

        best_index = None
        best_score = None

        for i, free in enumerate(free_rects):
            if w <= free["width"] and h <= free["height"]:
                leftover_w = free["width"] - w
                leftover_h = free["height"] - h
                short_side = min(leftover_w, leftover_h)
                long_side = max(leftover_w, leftover_h)
                score = (short_side, long_side)

                if best_score is None or score < best_score:
                    best_score = score
                    best_index = i

        if best_index is None:
            unplaced.append(job)
            continue

        free = free_rects.pop(best_index)
        x = free["x"]
        y = free["y"]

        placed.append(Rect(x, y, w, h, job))

        right = {
            "x": x + w + gap_px,
            "y": y,
            "width": free["x"] + free["width"] - (x + w + gap_px),
            "height": free["height"],
        }

        bottom = {
            "x": x,
            "y": y + h + gap_px,
            "width": free["width"],
            "height": free["y"] + free["height"] - (y + h + gap_px),
        }

        if right["width"] > 0 and right["height"] > 0:
            free_rects.append(right)

        if bottom["width"] > 0 and bottom["height"] > 0:
            free_rects.append(bottom)

        free_rects = _maxrects_prune_free_rects(free_rects)

    notes.append("MaxRects packing: mixed-size density-oriented layout.")

    return PackResult(placed, unplaced, "maxrects", notes)


def pack_jobs(
    jobs: List[dict],
    usable_width_px: int,
    usable_height_px: int,
    margin_px: int,
    gap_px: int,
    packing_mode: str = "auto",
) -> PackResult:
    mode = choose_packing_mode(jobs, packing_mode)

    if mode == "grid":
        return pack_grid(jobs, usable_width_px, usable_height_px, margin_px, gap_px)

    if mode == "shelf":
        return pack_shelf(jobs, usable_width_px, usable_height_px, margin_px, gap_px)

    if mode == "guillotine":
        return pack_guillotine(jobs, usable_width_px, usable_height_px, margin_px, gap_px)

    if mode == "maxrects":
        return pack_maxrects(jobs, usable_width_px, usable_height_px, margin_px, gap_px)

    return PackResult(
        placed=[],
        unplaced=jobs,
        mode_used=mode,
        notes=[f"Unknown packing mode: {mode}"],
    )