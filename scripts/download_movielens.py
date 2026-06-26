"""Download MovieLens dataset for collaborative filtering."""

import zipfile
from pathlib import Path

import requests
from tqdm import tqdm


def download_file(url: str, dest: Path):
    """Download file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with (
        open(dest, "wb") as f,
        tqdm(
            desc=dest.name,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))


def download_movielens(dataset: str = "ml-32m"):
    """
    Download MovieLens dataset.

    Args:
        dataset: Dataset name ('ml-32m', 'ml-latest-small', 'ml-latest')
            - ml-32m: 1 million ratings (6MB) - Recommended
            - ml-latest-small: 100K ratings (1MB) - For testing
            - ml-latest: 25 million ratings (265MB) - Large
    """
    datasets = {
        "ml-32m": "https://files.grouplens.org/datasets/movielens/ml-32m.zip",
        "ml-latest-small": "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip",
        "ml-latest": "https://files.grouplens.org/datasets/movielens/ml-latest.zip",
    }

    if dataset not in datasets:
        raise ValueError(
            f"Unknown dataset: {dataset}. Choose from: {list(datasets.keys())}"
        )

    url = datasets[dataset]
    data_dir = Path("data/movielens")
    data_dir.mkdir(exist_ok=True)

    zip_path = data_dir / f"{dataset}.zip"
    extract_dir = data_dir

    print(f"Downloading MovieLens {dataset}...")
    print(f"URL: {url}")
    print(f"Destination: {zip_path}\n")

    # Download
    download_file(url, zip_path)

    print(f"\nExtracting to {extract_dir}...")
    extract_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Extract to movielens/ (flatten structure)
        for member in zip_ref.namelist():
            # Skip directories
            if member.endswith("/"):
                continue

            # Get just the filename (remove directory prefix)
            filename = Path(member).name

            # Extract to movielens/ directory
            source = zip_ref.open(member)
            target = extract_dir / filename

            with open(target, "wb") as f:
                f.write(source.read())

    print(f"\n✅ Downloaded and extracted to: {extract_dir}")
    print("\nDataset contents:")

    for file in sorted(extract_dir.glob("*")):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name} ({size_mb:.1f} MB)")

    print(f"\n📝 You can now delete the zip file: {zip_path}")
    print("\nNext steps:")
    print("1. Run: python scripts/recommendation/movielens_cf.py")
    print("2. Or integrate into generate_recommendations.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download MovieLens dataset")
    parser.add_argument(
        "--dataset",
        default="ml-32m",
        choices=["ml-32m", "ml-latest-small", "ml-latest"],
        help="Dataset to download (default: ml-32m)",
    )

    args = parser.parse_args()

    try:
        download_movielens(args.dataset)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
