"""What this does: downloads newly painted pictures from fal into a chapter's paintings folder and
records each one in that folder's ledger (paintings.json): file, kind, size, the model and the
exact prompt and settings used, so the look can be matched later and any picture painted again.

Use: python3 -I save_fal_paintings.py PAINTINGS_FOLDER NEW_PAINTINGS.json
NEW_PAINTINGS.json is a list like:
  [{"name": "301-commons-field", "address": "https://v3b.fal.media/files/.../x.png",
    "request_id": "01a1...", "kind": "object", "aspect_ratio": "1:1", "resolution": "1k",
    "prompt": "A village common with grazing cows ... (the full prompt as sent)"}]
kind is "background", "figure" or "object". Pictures are saved as NAME.png (fal sends PNG).
"""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


def main():
    folder, new_list = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
    folder.mkdir(parents=True, exist_ok=True)
    ledger_path = folder / "paintings.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
        "note": "What this file is: every painting in this folder, with the exact request sent to fal to paint it.",
        "paintings": []}
    for item in new_list:
        destination = folder / f"{item['name']}.png"
        subprocess.run(["curl", "-sS", "--fail", "--max-time", "180", "-o", str(destination), item["address"]], check=True)
        with Image.open(destination) as picture:
            width, height = picture.size
        entry = {"file": destination.name, "mask": None, "kind": item["kind"], "width_px": width, "height_px": height,
                 "model": "fal: blackforestlabs/flux-3/text-to-image", "aspect_ratio": item.get("aspect_ratio"),
                 "resolution": item.get("resolution"), "request_id": item.get("request_id"), "prompt": item["prompt"],
                 "address": item["address"]}
        ledger["paintings"] = [e for e in ledger["paintings"] if e["file"] != entry["file"]] + [entry]
        print(f"saved {destination} ({width} x {height})")
    ledger_path.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
