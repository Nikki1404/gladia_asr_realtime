import argparse
import shutil
import tarfile
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download


MODEL_VARIANT = "64"

MODEL_MAP = {
    "en": {
        "download_type": "tar",
        "repo_id": "xumo/onnx_models",
        "filename": "sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2",
    },
    "es": {
        "download_type": "snapshot",
        "repo_id": "csukuangfj/sherpa-onnx-streaming-zipformer-es-kroko-2025-08-06",
    },
}

MODEL_FILE_PATTERNS = {
    "encoder.onnx": [
        "encoder.onnx",
        "encoder*.onnx",
    ],
    "decoder.onnx": [
        "decoder.onnx",
        "decoder*.onnx",
    ],
    "joiner.onnx": [
        "joiner.onnx",
        "joiner*.onnx",
    ],
    "tokens.txt": [
        "tokens.txt",
    ],
}


def safe_extract_tar(tar: tarfile.TarFile, output_dir: Path):
    output_dir = output_dir.resolve()

    for member in tar.getmembers():
        member_path = (output_dir / member.name).resolve()

        if not str(member_path).startswith(str(output_dir)):
            raise RuntimeError(f"Unsafe tar path detected: {member.name}")

    tar.extractall(output_dir)


def find_best_file(root: Path, patterns: list[str]) -> Path:
    matches = []

    for pattern in patterns:
        matches.extend(root.rglob(pattern))

    matches = [
        m
        for m in matches
        if m.is_file()
    ]

    if not matches:
        raise FileNotFoundError(
            f"Could not find file with patterns={patterns} under {root}"
        )

    fp32 = [
        m
        for m in matches
        if ".int8." not in m.name and "int8" not in m.name
    ]

    if fp32:
        matches = fp32

    preferred = [
        m
        for m in matches
        if "chunk-16-left-128" in m.name
    ]

    if preferred:
        return preferred[0]

    return matches[0]


def copy_required_files(source_root: Path, final_dir: Path):
    final_dir.mkdir(parents=True, exist_ok=True)

    print("Available model files:", flush=True)

    for p in sorted(source_root.rglob("*")):
        if p.is_file() and p.suffix in [".onnx", ".txt"]:
            print(f"  {p}", flush=True)

    for target_name, patterns in MODEL_FILE_PATTERNS.items():
        src = find_best_file(source_root, patterns)
        dst = final_dir / target_name

        print(f"Copying {src} -> {dst}", flush=True)
        shutil.copyfile(src, dst)

    print(f"Validated final model folder: {final_dir}", flush=True)


def download_tar_model(
    language: str,
    model_info: dict,
    models_root: Path,
):
    repo_id = model_info["repo_id"]
    filename = model_info["filename"]

    print(f"Downloading TAR model language={language}", flush=True)
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
        raise RuntimeError(f"Downloaded file is not tar archive: {downloaded_path}")

    with tarfile.open(downloaded_path, "r:*") as tar:
        safe_extract_tar(tar, extract_root)

    copy_required_files(extract_root, final_dir)

    print(f"Done language={language}", flush=True)


def download_snapshot_model(
    language: str,
    model_info: dict,
    models_root: Path,
):
    repo_id = model_info["repo_id"]

    print(f"Downloading SNAPSHOT model language={language}", flush=True)
    print(f"Repo: {repo_id}", flush=True)

    snapshot_root = snapshot_download(
        repo_id=repo_id,
        local_dir=str(models_root / "snapshots" / language),
        allow_patterns=[
            "encoder.onnx",
            "decoder.onnx",
            "joiner.onnx",
            "tokens.txt",
            "*.onnx",
            "*.txt",
        ],
    )

    snapshot_root = Path(snapshot_root)
    final_dir = models_root / "streaming_transducers" / MODEL_VARIANT / language

    copy_required_files(snapshot_root, final_dir)

    print(f"Done language={language}", flush=True)


def download_language(
    language: str,
    models_root: Path,
):
    if language not in MODEL_MAP:
        raise ValueError(
            f"Unsupported language={language}. "
            f"Supported: {list(MODEL_MAP.keys())}"
        )

    model_info = MODEL_MAP[language]
    download_type = model_info["download_type"]

    if download_type == "tar":
        download_tar_model(
            language=language,
            model_info=model_info,
            models_root=models_root,
        )

    elif download_type == "snapshot":
        download_snapshot_model(
            language=language,
            model_info=model_info,
            models_root=models_root,
        )

    else:
        raise ValueError(f"Unsupported download_type={download_type}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en", "es"],
    )

    parser.add_argument(
        "--models-root",
        default="models",
    )

    args = parser.parse_args()

    models_root = Path(args.models_root)

    for language in args.languages:
        download_language(
            language=language,
            models_root=models_root,
        )

    print("All requested models downloaded successfully.", flush=True)


if __name__ == "__main__":
    main()
