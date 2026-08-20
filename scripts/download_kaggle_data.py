"""
Download Olist Brazilian E-Commerce dataset from Kaggle.

This script authenticates with the Kaggle API, downloads the dataset,
and extracts it to the data/raw/ folder with idempotency checks.
"""

import hashlib
import json
import os
import zipfile
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


DATASET_NAME = "olistbr/brazilian-ecommerce"
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_FILE = DATA_RAW_DIR / ".download_manifest.json"


def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_manifest() -> dict:
    """Load the download manifest tracking file hashes."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r") as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict) -> None:
    """Save the download manifest."""
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)


def get_current_file_hashes() -> dict:
    """Get hashes of all CSV files in data/raw/."""
    hashes = {}
    if DATA_RAW_DIR.exists():
        for csv_file in DATA_RAW_DIR.glob("*.csv"):
            hashes[csv_file.name] = get_file_hash(csv_file)
    return hashes


def download_and_extract() -> list[str]:
    """Download dataset from Kaggle and extract to data/raw/."""
    print(f"Downloading dataset: {DATASET_NAME}")

    # Initialize and authenticate Kaggle API
    api = KaggleApi()
    api.authenticate()
    print("Authenticated with Kaggle API")

    # Ensure data/raw directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Download dataset as zip
    api.dataset_download_files(
        dataset=DATASET_NAME,
        path=DATA_RAW_DIR,
        unzip=False,
        quiet=False
    )

    # Find and extract the zip file
    zip_file = DATA_RAW_DIR / "brazilian-ecommerce.zip"
    if not zip_file.exists():
        raise FileNotFoundError(f"Expected zip file not found: {zip_file}")

    print(f"Extracting {zip_file.name}...")
    with zipfile.ZipFile(zip_file, "r") as zf:
        zf.extractall(DATA_RAW_DIR)

    # Remove zip file after extraction
    zip_file.unlink()
    print("Removed zip file after extraction")

    # Get list of extracted files
    extracted_files = sorted([f.name for f in DATA_RAW_DIR.glob("*.csv")])
    return extracted_files


def check_needs_download() -> bool:
    """Check if download is needed based on manifest and current files."""
    manifest = load_manifest()
    current_hashes = get_current_file_hashes()

    # If no manifest exists, we need to download
    if not manifest:
        print("No manifest found - download required")
        return True

    # If no files exist, we need to download
    if not current_hashes:
        print("No CSV files found - download required")
        return True

    # Compare hashes
    manifest_hashes = manifest.get("file_hashes", {})
    if manifest_hashes != current_hashes:
        print("File hashes don't match manifest - download required")
        return True

    print("Files match manifest - no download needed")
    return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("Kaggle Dataset Downloader")
    print(f"Dataset: {DATASET_NAME}")
    print(f"Target directory: {DATA_RAW_DIR}")
    print("=" * 60)

    # Check if download is needed (idempotency)
    if not check_needs_download():
        print("\nDataset already downloaded and up to date.")
        print("\nExisting files:")
        for csv_file in sorted(DATA_RAW_DIR.glob("*.csv")):
            size_mb = csv_file.stat().st_size / (1024 * 1024)
            print(f"  - {csv_file.name} ({size_mb:.2f} MB)")
        return

    # Download and extract
    print("\nStarting download...")
    extracted_files = download_and_extract()

    # Update manifest with new file hashes
    new_hashes = get_current_file_hashes()
    manifest = {
        "dataset": DATASET_NAME,
        "file_hashes": new_hashes
    }
    save_manifest(manifest)
    print("\nUpdated download manifest")

    # Print summary
    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)
    print(f"\nExtracted {len(extracted_files)} files to {DATA_RAW_DIR}:\n")

    for filename in extracted_files:
        filepath = DATA_RAW_DIR / filename
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"  - {filename} ({size_mb:.2f} MB)")

    total_size = sum(
        (DATA_RAW_DIR / f).stat().st_size for f in extracted_files
    ) / (1024 * 1024)
    print(f"\nTotal size: {total_size:.2f} MB")


if __name__ == "__main__":
    main()
