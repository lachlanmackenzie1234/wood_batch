from pathlib import Path
import csv
from collections import Counter
from typing import Dict, List

from packing import estimate_grid_capacity, pack_jobs


def summarize_jobs(jobs: List[dict]) -> Dict:
    total_items = len(jobs)
    total_area_px = sum(job["width_px"] * job["height_px"] for job in jobs)

    size_counts = Counter(
        (job["width_mm"], job["height_mm"], job["width_px"], job["height_px"])
        for job in jobs
    )

    return {
        "total_items": total_items,
        "total_area_px": total_area_px,
        "size_counts": size_counts,
    }


def print_capacity_report(
    jobs: List[dict],
    panel_width_px: int,
    panel_height_px: int,
    panel_width_mm: float,
    panel_height_mm: float,
    margin_px: int,
    gap_px: int,
    gap_mm: float,
    packing_result,
):
    usable_width_px = panel_width_px - (2 * margin_px)
    usable_height_px = panel_height_px - (2 * margin_px)
    usable_area_px = usable_width_px * usable_height_px

    summary = summarize_jobs(jobs)

    print("")
    print("Capacity report")
    print("---------------")
    print(f"Panel: {panel_width_mm} × {panel_height_mm} mm")
    print(f"Usable pixels: {usable_width_px} × {usable_height_px}")
    print(f"Gap: {gap_mm} mm")
    print(f"Requested items: {summary['total_items']}")
    print(f"Placed items: {len(packing_result.placed)}")
    print(f"Unplaced items: {len(packing_result.unplaced)}")
    print(f"Packing mode: {packing_result.mode_used}")

    if usable_area_px > 0:
        usage = summary["total_area_px"] / usable_area_px * 100
        print(f"Approx. item area usage: {usage:.1f}%")

    print("")
    print("Requested sizes:")

    for (width_mm, height_mm, width_px, height_px), count in summary["size_counts"].items():
        print(f"- {count} × {width_mm:g} × {height_mm:g} mm ({width_px} × {height_px} px)")

        if len(summary["size_counts"]) == 1:
            cols, rows, capacity = estimate_grid_capacity(
                usable_width_px,
                usable_height_px,
                width_px,
                height_px,
                gap_px,
            )
            print(f"  Grid estimate: {cols} × {rows} = {capacity} items")

    if packing_result.notes:
        print("")
        print("Packing notes:")
        for note in packing_result.notes:
            print(f"- {note}")

    print("")


def load_panel_presets(panels_csv_path: str = "panels.csv") -> List[dict]:
    path = Path(panels_csv_path)

    if not path.exists():
        return []

    panels = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            panels.append({
                "name": row["name"].strip(),
                "width_mm": float(row["width_mm"]),
                "height_mm": float(row["height_mm"]),
                "notes": row.get("notes", "").strip(),
            })

    return panels


def recommend_panel_presets(
    jobs: List[dict],
    panels: List[dict],
    dpi: int,
    outer_margin_mm: float,
    gap_mm: float,
    packing_mode: str = "auto",
):
    from template import mm_to_px

    if not panels:
        print("No panels.csv presets available for recommendation.")
        return

    margin_px = mm_to_px(outer_margin_mm, dpi)
    gap_px = mm_to_px(gap_mm, dpi)

    recommendations = []

    for panel in panels:
        panel_w_px = mm_to_px(panel["width_mm"], dpi)
        panel_h_px = mm_to_px(panel["height_mm"], dpi)

        usable_w_px = panel_w_px - (2 * margin_px)
        usable_h_px = panel_h_px - (2 * margin_px)

        result = pack_jobs(
            jobs=jobs,
            usable_width_px=usable_w_px,
            usable_height_px=usable_h_px,
            margin_px=margin_px,
            gap_px=gap_px,
            packing_mode=packing_mode,
        )

        usable_area = usable_w_px * usable_h_px
        item_area = sum(job["width_px"] * job["height_px"] for job in jobs)
        usage = (item_area / usable_area * 100) if usable_area > 0 else 0

        recommendations.append({
            "name": panel["name"],
            "width_mm": panel["width_mm"],
            "height_mm": panel["height_mm"],
            "placed": len(result.placed),
            "unplaced": len(result.unplaced),
            "usage": usage,
            "mode": result.mode_used,
            "fits_all": len(result.unplaced) == 0,
        })

    recommendations.sort(
        key=lambda r: (
            not r["fits_all"],
            r["width_mm"] * r["height_mm"],
            -r["placed"],
        )
    )

    print("")
    print("Panel recommendations")
    print("---------------------")

    for r in recommendations:
        status = "fits all" if r["fits_all"] else f"{r['unplaced']} unplaced"
        print(
            f"- {r['name']}: {r['width_mm']:g} × {r['height_mm']:g} mm, "
            f"{r['placed']} placed, {status}, "
            f"{r['usage']:.1f}% approx. usage, mode={r['mode']}"
        )

    print("")