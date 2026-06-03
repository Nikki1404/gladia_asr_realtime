import argparse
import shutil
import tarfile
from pathlib import Path

from huggingface_hub import hf_hub_download


# We keep our app folder layout:
# models/streaming_transducers/64/en/
# models/streaming_transducers/64/es/
MODEL_VARIANT = "64"

# Official sherpa-onnx models, not Kroko .data files.
# These are tar.bz2 archives and contain encoder/decoder/joiner/tokens.
MODEL_MAP = {
    "en": {
        "repo_id": "csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26",
        "filename": "sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2",
    },
    "es": {
        # Spanish streaming zipformer model.
        # If this repo/file is unavailable in your network, use --languages en first,
        # then we can swap Spanish to another available sherpa-onnx Spanish model.
        "repo_id": "csukuangfj/sherpa-onnx-streaming-zipformer-es-2024-01-04",
        "filename": "sherpa-onnx-streaming-zipformer-es-2024-01-04.tar.bz2",
    },
}

REQUIRED_FILES = ["encoder.onnx", "decoder.onnx", "joiner.onnx", "tokens.txt"]


def safe_extract_tar(tar: tarfile.TarFile, output_dir: Path):
    output_dir = output_dir.resolve()

    for member in tar.getmembers():
        member_path = (output_dir / member.name).resolve()
        if not str(member_path).startswith(str(output_dir)):
            raise RuntimeError(f"Unsafe tar path detected: {member.name}")

    tar.extractall(output_dir)


def find_and_copy_required_files(extracted_dir: Path, final_dir: Path):
    final_dir.mkdir(parents=True, exist_ok=True)

    for filename in REQUIRED_FILES:
        matches = list(extracted_dir.rglob(filename))

        if not matches:
            raise FileNotFoundError(
                f"Could not find {filename} under extracted folder: {extracted_dir}"
            )

        src = matches[0]
        dst = final_dir / filename

        print(f"Copying {src} -> {dst}", flush=True)
        shutil.copyfile(src, dst)

    print(f"Validated final model folder: {final_dir}", flush=True)


def download_language(language: str, models_root: Path):
    if language not in MODEL_MAP:
        raise ValueError(
            f"Unsupported language={language}. Supported: {list(MODEL_MAP.keys())}"
        )

    repo_id = MODEL_MAP[language]["repo_id"]
    filename = MODEL_MAP[language]["filename"]

    print(f"Downloading language={language}", flush=True)
    print(f"Repo: {repo_id}", flush=True)
    print(f"File: {filename}", flush=True)

    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(models_root / "downloads"),
    )

    downloaded_path = Path(downloaded_path)

    extract_root = models_root / "extracted" / language
    final_dir = models_root / "streaming_transducers" / MODEL_VARIANT / language

    if extract_root.exists():
        shutil.rmtree(extract_root)

    extract_root.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {downloaded_path} -> {extract_root}", flush=True)

    if not tarfile.is_tarfile(downloaded_path):
        raise RuntimeError(f"Downloaded file is not a tar archive: {downloaded_path}")

    with tarfile.open(downloaded_path, "r:*") as tar:
        safe_extract_tar(tar, extract_root)

    find_and_copy_required_files(extract_root, final_dir)

    print(f"Done language={language}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="+", default=["en"])
    parser.add_argument("--models-root", default="models")
    args = parser.parse_args()

    models_root = Path(args.models_root)

    for language in args.languages:
        download_language(language=language, models_root=models_root)

    print("All requested models downloaded successfully.", flush=True)


if __name__ == "__main__":
    main()
