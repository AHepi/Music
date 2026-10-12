"""What this does: downloads the cut-out masks that fal's background remover made, gives each one a
plain name next to its painting, and notes it in the paintings ledger if there is one.

The masks are black-and-white pictures: white where the figure or object is, black where the plain
grey background was. Each is saved in the paintings folder's "masks" folder as "NAME-mask.png",
where NAME is the painting's file name without its ending (for example 301-commons-field).

Use: python3 -I download_fal_masks.py PAINTINGS_FOLDER NAME=MASK_ADDRESS [NAME=MASK_ADDRESS ...]
Example: python3 -I paper-film/tools/download_fal_masks.py assets/paintings/enclosures-1 \
           301-commons-field=https://v3b.fal.media/files/.../mask.png
If PAINTINGS_FOLDER holds a paintings.json ledger (a list under "paintings", each with a "file"),
the matching entry gets "mask" and "mask_address" filled in.
"""

import json
import subprocess
import sys
from pathlib import Path


def download_file(address, destination):
    """Downloads one file with curl and checks it is a real PNG picture, not an error page."""
    subprocess.run(["curl", "-sS", "--fail", "--max-time", "120", "-o", str(destination), address], check=True)
    with open(destination, "rb") as downloaded:
        first_bytes = downloaded.read(8)
    if first_bytes != b"\x89PNG\r\n\x1a\n":
        destination.unlink()
        raise SystemExit(f"{address} did not give a PNG picture.")


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Use: download_fal_masks.py PAINTINGS_FOLDER NAME=MASK_ADDRESS [...]")
    folder = Path(sys.argv[1])
    (folder / "masks").mkdir(parents=True, exist_ok=True)
    ledger_path = folder / "paintings.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else None
    for pair in sys.argv[2:]:
        name, address = pair.split("=", 1)
        destination = folder / "masks" / f"{name}-mask.png"
        download_file(address, destination)
        print(f"saved {destination}")
        if ledger:
            for entry in ledger.get("paintings", []):
                if Path(entry.get("file", "")).stem == name:
                    entry["mask"] = f"masks/{name}-mask.png"
                    entry["mask_address"] = address
    if ledger:
        ledger_path.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
