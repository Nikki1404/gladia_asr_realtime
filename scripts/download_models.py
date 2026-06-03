import argparse
import shutil
import tarfile
import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "Banafo/Kroko-ASR"

# Kroko model variant folder.
# This is NOT client realtime streaming chunk size.
MODEL_VARIANT = "64"

MODEL_MAP = {
    "en": "Kroko-EN-Community-64-L-Streaming-001.data",
    "es": "Kroko-ES-Community-64-L-Streaming-001.data",
}

REQUIRED_FILES = ["encoder.onnx", "decoder.onnx", "joiner.onnx", "tokens.txt"]


def safe_extract_tar(tar: tarfile.TarFile, output_dir: Path):
    output_dir = output_dir.resolve()
    for member in tar.getmembers():
        member_path = (output_dir / member.name).resolve()
        if not str(member_path).startswith(str(output_dir)):
            raise RuntimeError(f"Unsafe tar path detected: {member.name}")
    tar.extractall(output_dir)


def extract_archive(data_file: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {data_file} -> {output_dir}", flush=True)

    if tarfile.is_tarfile(data_file):
        with tarfile.open(data_file, "r:*") as tar:
            safe_extract_tar(tar, output_dir)
        return

    if zipfile.is_zipfile(data_file):
        with zipfile.ZipFile(data_file, "r") as zf:
            zf.extractall(output_dir)
        return

    raise RuntimeError(
        f"Unsupported model archive format: {data_file}. Expected tar or zip-like .data archive."
    )


def normalize_files(output_dir: Path):
    for filename in REQUIRED_FILES:
        target = output_dir / filename
        if target.exists():
            continue

        matches = list(output_dir.rglob(filename))
        if not matches:
            raise FileNotFoundError(f"Could not find {filename} inside {output_dir}")

        source = matches[0]
        print(f"Copying {source} -> {target}", flush=True)
        shutil.copyfile(source, target)

    print(f"Validated model folder: {output_dir}", flush=True)


def download_language(language: str, models_root: Path):
    if language not in MODEL_MAP:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(MODEL_MAP)}")

    filename = MODEL_MAP[language]
    print(f"Downloading language={language}, file={filename}", flush=True)

    downloaded = hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        local_dir=str(models_root / "downloads"),
        local_dir_use_symlinks=False,
    )

    downloaded_path = Path(downloaded)
    output_dir = models_root / "streaming_transducers" / MODEL_VARIANT / language

    extract_archive(downloaded_path, output_dir)
    normalize_files(output_dir)

    print(f"Done language={language}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="+", default=["en", "es"])
    parser.add_argument("--models-root", default="models")
    args = parser.parse_args()

    models_root = Path(args.models_root)

    for language in args.languages:
        download_language(language=language, models_root=models_root)

    print("All requested models downloaded successfully.", flush=True)


if __name__ == "__main__":
    main()
