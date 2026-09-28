"""Run inside WSL as root: print a JSON inventory of SDK record and workspace files."""
import hashlib
import json
import os
from datetime import datetime, timezone

ROOTS = ("/home/evidex/records", "/home/evidex/isolated")
inventory = []
for root in ROOTS:
    for directory, _, names in os.walk(root):
        for name in names:
            path = os.path.join(directory, name)
            if os.path.islink(path):
                inventory.append({"path": path, "symlink": True})
                continue
            with open(path, "rb") as handle:
                data = handle.read()
            stat = os.stat(path)
            inventory.append({
                "path": path,
                "size": stat.st_size,
                "sha256": hashlib.sha256(data).hexdigest(),
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            })
print(json.dumps(sorted(inventory, key=lambda item: item["path"])))
