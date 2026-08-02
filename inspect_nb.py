 """temporary inspection script for notebooks"""
import json

for path in [
    "draft 1 wms.ipynb",
    "models.ipynb",
]:
    print("=" * 70)
    print(path)
    print("=" * 70)
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    print("total cells:", len(nb["cells"]))
    for i, c in enumerate(nb["cells"]):
        head = "".join(c["source"])[:120].replace("\n", " / ")
        print(f"[{i}] {c['cell_type'].upper()}: {head}")

