# Wood Batch Template Generator

This project generates print-ready PNG panels for wood/magnet production.

The workflow is:

```text
1. Put source images into images/
2. Edit jobs.csv with file names, quantities, and final print sizes
3. Choose a panel preset in config.csv, or enter a custom panel size
4. Run run.sh on macOS, or run.bat on Windows
5. Collect the generated panel from output/
```

## Project files

```text
wood_batch/
├── images/              Source images go here
├── output/              Generated print panels are saved here
├── jobs.csv             Production list: image, quantity, item size
├── config.csv           Export settings: DPI, margins, gaps, panel preset
├── panels.csv           Reusable panel size presets
├── packing.py           Packing algorithms: grid, shelf, guillotine, maxrects
├── planner.py           Capacity report and panel recommendations
├── requirements.txt     Python package requirements
├── run.sh               macOS / Linux runner
├── run.bat              Windows runner
└── template.py          Panel generation script
```

## Install Python

Python must be installed before running this project.

### macOS

Install Python from:

```text
https://www.python.org/downloads/macos/
```

Or with Homebrew:

```bash
brew install python
```

### Windows

Install Python from:

```text
https://www.python.org/downloads/windows/
```

During installation, tick:

```text
Add python.exe to PATH
```

Then close and reopen the folder before running `run.bat`.

## First-time setup

`requirements.txt` should contain:

```txt
Pillow>=10.4,<12
```

`Pillow` is the imaging library used by `template.py`. In Python code it is imported as `PIL`, but the package name installed by pip is `Pillow`.

The runner scripts install this automatically into a local `.venv` folder.

## Edit `jobs.csv`

Each row describes one image batch.

```csv
file,quantity,width_mm,height_mm
image_1.png,10,25,25
image_2.png,25,25,25
image_3.png,8,50,50
```

Meaning:

```text
file       Source image inside images/
quantity   Number of copies to place on the panel
width_mm   Final printed width of each item, not the source image width
height_mm  Final printed height of each item, not the source image height
```

The file names in `jobs.csv` must exactly match the files inside `images/`.

## Edit `config.csv`

`config.csv` controls export-wide settings.

```csv
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
```

Meaning:

```text
panel_preset         Name of a preset from panels.csv.
dpi                  Print resolution. MIPP recommends 300 DPI minimum for high resolution.
panel_width_mm       Optional manual panel width. Leave blank to use panel_preset.
panel_height_mm      Optional manual panel height. Leave blank to use panel_preset.
outer_margin_mm      Safe margin around the whole panel.
gap_mm               Space between each image for cutting/sawing.
output_file          Export path. Existing files are not overwritten; a number is added automatically.
fit_mode             cover crops to fill; contain fits the full image with padding.
packing_mode         auto, grid, shelf, guillotine, or maxrects.
show_capacity_report true/false. Prints item count, panel usage, and grid estimates.
recommend_panel      true/false. Tests presets from panels.csv and prints recommendations.
draw_cut_guides      true/false. Adds faint outlines around each item.
draw_labels          true/false. Adds file names on top of images for testing.
```

If `panel_width_mm` or `panel_height_mm` are filled in, those manual values override the selected preset.

For a first test run, it can be useful to set:

```csv
draw_cut_guides,true
draw_labels,true
```

For production, set both back to `false` unless guides or labels are specifically wanted.

## Packing modes

`packing_mode` controls how items are placed on the panel.

```text
auto        Chooses a packing mode based on jobs.csv.
grid        Best for one item size, for example 288 × 100×100 mm.
shelf       Simple predictable row-based layout.
guillotine  Cut-friendly layout for divisible sizes such as 25, 50, and 100 mm.
maxrects    Denser layout for mixed sizes, but less cut-oriented.
```

Recommended default:

```csv
packing_mode,auto
```

For most one-size templates, `auto` should select `grid`. For mixed but divisible sizes, `auto` should select `guillotine`.

The script can also print a capacity report:

```csv
show_capacity_report,true
```

To compare all presets from `panels.csv`, set:

```csv
recommend_panel,true
```

This does not change the selected panel automatically; it only prints recommendations in the terminal.

## Edit `panels.csv`

`panels.csv` stores reusable panel sizes.

```csv
name,width_mm,height_mm,notes
standard_600x1200,600,1200,Safe general default panel
large_720x1500,720,1500,Matches visualpanel_foot_001 if treated as 240 DPI physical size
extra_large_1250x2500,1250,2500,Matches visualpanel_kit_5x5_72 and panel_10x10_001_pilat physical size
wide_2000x1000,2000,1000,Wide landscape panel for horizontal layouts
square_1200x1200,1200,1200,Square test panel
```

To use a preset, set `panel_preset` in `config.csv`:

```csv
panel_preset,extra_large_1250x2500
```

To use a custom one-off panel size, leave `panel_preset` blank and set `panel_width_mm` and `panel_height_mm` manually in `config.csv`:

```csv
panel_preset,
panel_width_mm,1200
panel_height_mm,1200
```

## Run on macOS

From Terminal:

```bash
cd ~/Downloads/wood_batch
chmod +x run.sh
./run.sh
```

`run.sh` will create a local `.venv`, install dependencies, and run `template.py`.

## Run on Windows

Double-click:

```text
run.bat
```

Or run from PowerShell:

```powershell
.\run.bat
```

`run.bat` will create a local `.venv`, install dependencies, and run `template.py`.

## Output

Generated panels are saved in:

```text
output/
```

The default export is a PNG at the DPI set in `config.csv`.

Existing files are not overwritten. For example, if this file already exists:

```text
output/panel.png
```

The next export will be saved as:

```text
output/panel_1.png
```

Then:

```text
output/panel_2.png
```

## Capacity report

When `show_capacity_report` is `true`, the script prints a summary after each run.

Example:

```text
Capacity report
---------------
Panel: 1250 × 2500 mm
Requested items: 288
Placed items: 288
Unplaced items: 0
Packing mode: grid
Approx. item area usage: 92.2%
Grid estimate: 12 × 24 = 288 items
```

This is useful for confirming that the selected panel size, quantities, and item sizes match expectations before sending the file to print.
```

## Print settings

Current default print setting:

```text
DPI: 300
```

Useful conversion:

```text
pixels = millimetres / 25.4 × DPI
```

Examples at 300 DPI:

```text
25 mm  = 295 px
50 mm  = 591 px
100 mm = 1181 px
120 mm = 1417 px
```

## MIPP technical notes

The MIPP technical sheet recommends:

```text
300 DPI minimum for high-resolution images
3 mm minimum bleed / fonds perdus around final cut size
5 mm internal safe zone away from the cut edge
```

This generator currently treats `gap_mm` as the space between items for cutting/sawing and `outer_margin_mm` as the safe margin around the full panel.

Before production, run once with `draw_cut_guides,true` and confirm the panel size, item count, and spacing.

## Notes

- Use high-resolution source images whenever possible.
- PNG is preferred because it is lossless.
- JPEG can introduce compression artifacts and should only be used if specifically required.
- ImageMagick is optional and only useful for inspecting existing image metadata. It is not required to generate panels.

---
