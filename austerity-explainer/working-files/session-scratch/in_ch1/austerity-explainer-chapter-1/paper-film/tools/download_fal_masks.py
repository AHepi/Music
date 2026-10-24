"""
What this does: downloads the cut-out masks that fal's background remover made, gives each one a
plain name, and writes down where it came from.

The masks are black-and-white pictures: white where the figure or object is, black where the
plain grey background was. They are saved next to the painted pictures, in a "masks" folder, as
"NNN-name-mask.png", where NNN and name are the painted picture's number and name.

Usage:
    python3 -I download_fal_masks.py PICTURE_FOLDER 1203=URL 1204=URL ...

The number before "=" is 1000 plus the painted picture's number (1203 is the mask for picture 203).
The ledger "00-requests.json" in PICTURE_FOLDER supplies the picture's name and gets each mask's
address added under "masks".
"""

import json
import subprocess
import sys
from pathlib import Path


def picture_name_for_number(ledger, picture_number):
    """Finds a painted picture's name in the ledger, for example 203 -> 'munition-women'."""
    for section in ("flux3", "repaints"):
        entries = ledger.get(section, {})
        if str(picture_number) in entries:
            return entries[str(picture_number)][0]
    raise SystemExit(f"Picture {picture_number} is not in the ledger.")


def download_file(address, destination):
    """Downloads one file with curl and checks it is a real picture, not an error page."""
    subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "120", "-o", str(destination), address],
        check=True,
    )
    with open(destination, "rb") as downloaded:
        first_bytes = downloaded.read(8)
    if first_bytes != b"\x89PNG\r\n\x1a\n":
        destination.unlink()
        raise SystemExit(f"{address} did not give a picture file.")


def main():
    picture_folder = Path(sys.argv[1])
    ledger_path = picture_folder / "00-requests.json"
    ledger = json.loads(ledger_path.read_text())
    mask_folder = picture_folder / "masks"
    mask_folder.mkdir(exist_ok=True)
    ledger.setdefault("masks", {})

    for pair in sys.argv[2:]:
        mask_number_text, address = pair.split("=", 1)
        picture_number = int(mask_number_text) - 1000
        picture_name = picture_name_for_number(ledger, picture_number)
        destination = mask_folder / f"{picture_number}-{picture_name}-mask.png"
        download_file(address, destination)
        ledger["masks"][str(picture_number)] = [destination.name, address]
        print(f"saved {destination.name}")

    ledger_path.write_text(json.dumps(ledger, indent=1) + "\n")


if __name__ == "__main__":
    main()
