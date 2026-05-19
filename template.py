from PIL import Image, ImageOps, ImageDraw
from pathlib import Path
import csv
from packing import pack_jobs
from planner import print_capacity_report, load_panel_presets, recommend_panel_presets

# =========================
# DEFAULT SETTINGS
# =========================
# These defaults are used if config.csv is missing or a value is blank.

DEFAULT_DPI = 300
DEFAULT_PANEL_WIDTH_MM = 600
DEFAULT_PANEL_HEIGHT_MM = 1200
DEFAULT_OUTER_MARGIN_MM = 5
DEFAULT_GAP_MM = 3

CONFIG_CSV = "config.csv"
PANELS_CSV = "panels.csv"
JOBS_CSV = "jobs.csv"
IMAGE_FOLDER = "images"
OUTPUT_FILE = "output/print_panel.png"

BACKGROUND = "white"

# "cover" = crop to fill each tile
# "contain" = show full image with padding
FIT_MODE = "cover"

DRAW_CUT_GUIDES = False
CUT_GUIDE_COLOR = (180, 180, 180)
CUT_GUIDE_WIDTH_PX = 1

DRAW_LABELS = False


# =========================
# HELPERS
# =========================

def mm_to_px(mm, dpi):
    return round((float(mm) / 25.4) * dpi)


def parse_bool(value, default=False):
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in ["1", "true", "yes", "y", "on"]


def load_config():
    """
    Optional config.csv format:

    key,value
    panel_preset,standard_600x1200
    dpi,300
    panel_width_mm,
    panel_height_mm,
    outer_margin_mm,5
    gap_mm,3
    output_file,output/panel.png
    fit_mode,cover
    packing_mode,auto
    show_capacity_report,true
    recommend_panel,false
    draw_cut_guides,false
    draw_labels,false
    """
    config = {
        "panel_preset": "",
        "dpi": DEFAULT_DPI,
        "panel_width_mm": DEFAULT_PANEL_WIDTH_MM,
        "panel_height_mm": DEFAULT_PANEL_HEIGHT_MM,
        "outer_margin_mm": DEFAULT_OUTER_MARGIN_MM,
        "gap_mm": DEFAULT_GAP_MM,
        "output_file": OUTPUT_FILE,
        "fit_mode": FIT_MODE,
        "packing_mode": "auto",
        "show_capacity_report": True,
        "recommend_panel": False,
        "draw_cut_guides": DRAW_CUT_GUIDES,
        "draw_labels": DRAW_LABELS,
    }

    config_path = Path(CONFIG_CSV)
    if not config_path.exists():
        return config

    with config_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("key", "").strip()
            value = row.get("value", "").strip()

            if not key or value == "":
                continue

            if key == "dpi":
                config[key] = int(float(value))
            elif key in ["panel_width_mm", "panel_height_mm", "outer_margin_mm", "gap_mm"]:
                config[key] = float(value)
            elif key in ["draw_cut_guides", "draw_labels", "show_capacity_report", "recommend_panel"]:
                config[key] = parse_bool(value, config[key])
            elif key in ["panel_preset", "output_file", "fit_mode", "packing_mode"]:
                config[key] = value
            else:
                print(f"Warning: unknown config key ignored: {key}")

    return config


def config_has_manual_panel_size(key_name):
    config_path = Path(CONFIG_CSV)
    if not config_path.exists():
        return False

    with config_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("key", "").strip()
            value = row.get("value", "").strip()
            if key == key_name and value != "":
                return True

    return False


def apply_panel_preset(config):
    """
    Optional panels.csv format:

    name,width_mm,height_mm,notes
    standard_600x1200,600,1200,Safe general default panel
    large_720x1500,720,1500,Matches one historical panel size
    extra_large_1250x2500,1250,2500,Matches common historical panels

    If config.csv has panel_preset set, that preset controls panel_width_mm and panel_height_mm.
    If panel_width_mm or panel_height_mm are manually set in config.csv, those manual values take priority.
    """
    preset_name = str(config.get("panel_preset", "")).strip()
    if not preset_name:
        return config

    panels_path = Path(PANELS_CSV)
    if not panels_path.exists():
        print(f"Warning: panel_preset is set to '{preset_name}', but {PANELS_CSV} was not found.")
        return config

    manual_width = config_has_manual_panel_size("panel_width_mm")
    manual_height = config_has_manual_panel_size("panel_height_mm")

    with panels_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            if name != preset_name:
                continue

            if not manual_width:
                config["panel_width_mm"] = float(row["width_mm"])
            if not manual_height:
                config["panel_height_mm"] = float(row["height_mm"])

            print(f"Using panel preset: {preset_name}")
            return config

    print(f"Warning: panel_preset '{preset_name}' was not found in {PANELS_CSV}.")
    return config


def resize_to_tile(img, target_size, mode="cover"):
    if mode == "cover":
        return ImageOps.fit(
            img,
            target_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )

    if mode == "contain":
        fitted = ImageOps.contain(
            img,
            target_size,
            method=Image.Resampling.LANCZOS
        )
        canvas = Image.new("RGB", target_size, BACKGROUND)
        x = (target_size[0] - fitted.width) // 2
        y = (target_size[1] - fitted.height) // 2
        canvas.paste(fitted, (x, y))
        return canvas

    raise ValueError("fit_mode must be 'cover' or 'contain'.")


def load_jobs(dpi):
    jobs = []

    with open(JOBS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            filename = row["file"].strip()
            quantity = int(row["quantity"])
            width_mm = float(row["width_mm"])
            height_mm = float(row["height_mm"])

            for _ in range(quantity):
                jobs.append({
                    "file": filename,
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                    "width_px": mm_to_px(width_mm, dpi),
                    "height_px": mm_to_px(height_mm, dpi),
                })

    return jobs


def get_available_output_path(output_path):
    output_path = Path(output_path)

    if not output_path.exists():
        return output_path

    parent = output_path.parent
    stem = output_path.stem
    suffix = output_path.suffix

    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def save_output(img, output_path, dpi):
    output_path = get_available_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lower()

    if suffix in [".jpg", ".jpeg"]:
        img.save(
            output_path,
            dpi=(dpi, dpi),
            quality=95,
            subsampling=0,
            optimize=True
        )
    elif suffix in [".tif", ".tiff"]:
        img.save(
            output_path,
            dpi=(dpi, dpi),
            compression="tiff_lzw"
        )
    else:
        img.save(
            output_path,
            dpi=(dpi, dpi),
            compress_level=6
        )

    return output_path


def main():
    config = apply_panel_preset(load_config())

    dpi = config["dpi"]
    panel_width_mm = config["panel_width_mm"]
    panel_height_mm = config["panel_height_mm"]
    outer_margin_mm = config["outer_margin_mm"]
    gap_mm = config["gap_mm"]
    output_file = config["output_file"]
    fit_mode = config["fit_mode"]
    packing_mode = config["packing_mode"]
    show_capacity_report = config["show_capacity_report"]
    recommend_panel = config["recommend_panel"]
    draw_cut_guides = config["draw_cut_guides"]
    draw_labels = config["draw_labels"]

    panel_w_px = mm_to_px(panel_width_mm, dpi)
    panel_h_px = mm_to_px(panel_height_mm, dpi)
    margin_px = mm_to_px(outer_margin_mm, dpi)
    gap_px = mm_to_px(gap_mm, dpi)

    jobs = load_jobs(dpi)

    usable_width_px = panel_w_px - (2 * margin_px)
    usable_height_px = panel_h_px - (2 * margin_px)

    packing_result = pack_jobs(
        jobs=jobs,
        usable_width_px=usable_width_px,
        usable_height_px=usable_height_px,
        margin_px=margin_px,
        gap_px=gap_px,
        packing_mode=packing_mode,
    )

    canvas = Image.new("RGB", (panel_w_px, panel_h_px), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    image_cache = {}

    for rect in packing_result.placed:
        job = rect.job
        img_path = Path(IMAGE_FOLDER) / job["file"]

        if img_path not in image_cache:
            if not img_path.exists():
                raise FileNotFoundError(f"Missing image: {img_path}")

            source = Image.open(img_path)
            source = ImageOps.exif_transpose(source)
            source = source.convert("RGB")
            image_cache[img_path] = source

        source = image_cache[img_path]
        tile = resize_to_tile(source, (rect.width, rect.height), fit_mode)

        canvas.paste(tile, (rect.x, rect.y))

        if draw_cut_guides:
            draw.rectangle(
                [rect.x, rect.y, rect.x + rect.width, rect.y + rect.height],
                outline=CUT_GUIDE_COLOR,
                width=CUT_GUIDE_WIDTH_PX
            )

        if draw_labels:
            draw.text((rect.x + 5, rect.y + 5), job["file"], fill=(0, 0, 0))

    saved_output_path = save_output(canvas, output_file, dpi)

    if show_capacity_report:
        print_capacity_report(
            jobs=jobs,
            panel_width_px=panel_w_px,
            panel_height_px=panel_h_px,
            panel_width_mm=panel_width_mm,
            panel_height_mm=panel_height_mm,
            margin_px=margin_px,
            gap_px=gap_px,
            gap_mm=gap_mm,
            packing_result=packing_result,
        )

    if recommend_panel:
        panels = load_panel_presets(PANELS_CSV)
        recommend_panel_presets(
            jobs=jobs,
            panels=panels,
            dpi=dpi,
            outer_margin_mm=outer_margin_mm,
            gap_mm=gap_mm,
            packing_mode=packing_mode,
        )

    print("Export complete")
    print(f"Output: {saved_output_path.resolve()}")
    if config.get("panel_preset"):
        print(f"Panel preset: {config['panel_preset']}")
    print(f"Panel: {panel_width_mm} × {panel_height_mm} mm")
    print(f"Pixels: {panel_w_px} × {panel_h_px} px at {dpi} DPI")
    print(f"Gap: {gap_mm} mm")
    print(f"Outer margin / safe area: {outer_margin_mm} mm")
    print(f"Packing mode: {packing_result.mode_used}")
    print(f"Placed: {len(packing_result.placed)}")
    print(f"Unplaced: {len(packing_result.unplaced)}")

    if packing_result.unplaced:
        print("\nThe following items did not fit:")
        for item in packing_result.unplaced:
            print(f"- {item['file']} {item['width_mm']} × {item['height_mm']} mm")


if __name__ == "__main__":
    main()