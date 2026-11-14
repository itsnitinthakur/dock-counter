# Dock Counter: count goods in and out during loading and unloading

A camera over the store door or dock counts bags, cartons or rolls as they cross a line. Optional weights give a second estimate. The result is compared with the Odoo receipt or delivery, and a note with photos is posted for the storekeeper to confirm.

## Files
| File | What it does |
|---|---|
| `line_counter.py` | Counts tracked objects crossing a line, once each, in or out (tested) |
| `dock_counter.py` | Reads a video or CCTV stream, detects and tracks items with YOLO, counts, saves a photo per item |
| `weight_estimate.py` | Estimates units from weighbridge or platform-scale weights (tested) |
| `odoo_push.py` | Compares count with the Odoo transfer and posts a note and photo; never validates on its own |
| `test_*.py` | Tests: run `python -m pytest -q` |

## Setup (Mac)
```bash
python3 -m venv ~/dock-env && source ~/dock-env/bin/activate
pip install -r requirements.txt
python -m pytest -q          # 10 tests should pass
```

## Step 1: try it on a video
Record a phone video of unloading from where a camera would go (above the door, looking down). Then:
```bash
python dock_counter.py --source unloading.mp4 --line 100 400 1180 400 --show
```
Pick the line so items cross it one way when coming in. Press `q` to stop.

The default model is a general one. It knows people, not sacks, so expect poor counts until Step 2.

## Step 2: train a model on your own bags and cartons
1. Pull about 300-500 frames from several unloading videos (different times of day, bag types, angles).
2. Label each bag or carton with a box, using a labelling tool such as Label Studio or CVAT, exported in YOLO format.
3. Create `bags.yaml` listing the image folders and class names (for example `bag`, `carton`, `roll`).
4. Train:
   ```bash
   yolo detect train data=bags.yaml model=yolo11n.pt epochs=100 imgsz=640
   ```
5. Use the result: `--model runs/detect/train/weights/best.pt`

## Step 3: measure accuracy before trusting it
For 10 real truck loads, count by hand and by the system. Record both. Aim for the system to be within 1-2% before using it for receipts.

## Step 4: send to Odoo (test database first)
```bash
export ODOO_URL=http://localhost:8069 ODOO_DB=wh_lab ODOO_USER=admin ODOO_PASSWORD=yourpassword
python dock_counter.py --source unloading.mp4 --model best.pt --line 100 400 1180 400 \
    --picking WH/IN/00012 --push
```
The receipt gets a note like "Camera count: SHORT. Expected 200, Counted 196, Difference -4" plus a photo.
Weight estimate example: `python weight_estimate.py`.

## Camera placement tips
- Mount above the door or dock, looking down, so items don't hide behind each other.
- Keep the counting line where items pass one at a time (a door, a ramp, a conveyor).
- Add light over the dock for night shifts.
- Point the camera at the goods, not at faces. Tell staff what the camera is for.
# dock-counter
