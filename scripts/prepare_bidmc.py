"""Prepara subconjunto público BIDMC sem misturá-lo às fixtures sintéticas."""

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

BASE = "https://physionet.org/files/bidmc/1.0.0/"
ROOT = Path(__file__).resolve().parents[1] / "data/external/bidmc"
PARTITIONS = {"development": (1, 2), "validation": (3, 4), "test": (5, 6)}


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    files = []
    for split, subjects in PARTITIONS.items():
        for subject in subjects:
            name = f"bidmc_{subject:02d}_Numerics.csv"
            url = BASE + "bidmc_csv/" + name
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read()
            (ROOT / name).write_bytes(content)
            files.append(
                {
                    "path": name,
                    "url": url,
                    "sha256": checksum(content),
                    "source_group": f"BIDMC-{subject:02d}",
                    "split": split,
                }
            )
    with urllib.request.urlopen(BASE + "LICENSE", timeout=30) as response:
        license_content = response.read()
    (ROOT / "LICENSE").write_bytes(license_content)
    manifest = {
        "source": "https://physionet.org/content/bidmc/1.0.0/",
        "version": "1.0.0",
        "license": "ODC-By-1.0",
        "license_sha256": checksum(license_content),
        "citation": "Pimentel et al. (2016), doi:10.1109/TBME.2016.2613124",
        "synthetic": False,
        "cloud_upload_allowed": False,
        "purpose": "real_signal_ingestion_only_no_anomaly_ground_truth",
        "missing_requirement": "blood pressure is not included in this subset",
        "files": files,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def validate() -> dict[str, object]:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    if checksum((ROOT / "LICENSE").read_bytes()) != manifest["license_sha256"]:
        raise ValueError("license checksum mismatch")
    groups: set[str] = set()
    hashes: set[str] = set()
    rows_by_split = dict.fromkeys(PARTITIONS, 0)
    for item in manifest["files"]:
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise ValueError("external path escapes dataset root")
        content = path.read_bytes()
        if checksum(content) != item["sha256"]:
            raise ValueError("external checksum mismatch")
        if item["source_group"] in groups or item["sha256"] in hashes:
            raise ValueError("duplicate external source/content")
        groups.add(item["source_group"])
        hashes.add(item["sha256"])
        rows = csv.DictReader(io.StringIO(content.decode()))
        if rows.fieldnames is None or not {"Time [s]", " HR", " SpO2"}.issubset(
            rows.fieldnames
        ):
            raise ValueError("unexpected BIDMC columns")
        last_time = -1.0
        for row in rows:
            time = float(row["Time [s]"])
            if not math.isfinite(time) or time <= last_time:
                raise ValueError("invalid external time ordering")
            last_time = time
            rows_by_split[item["split"]] += 1
    if len(groups) != 6 or any(count == 0 for count in rows_by_split.values()):
        raise ValueError("incomplete external subset")
    return {
        "records": len(groups),
        "rows_by_split": rows_by_split,
        "has_anomaly_labels": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["download", "validate"])
    args = parser.parse_args()
    if args.command == "download":
        download()
    print(json.dumps(validate(), indent=2))
