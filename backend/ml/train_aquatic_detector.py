"""Audit a Roboflow YOLO dataset and train AquaGuard's aquatic behaviour model."""

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from ultralytics import YOLO

from app.core.config import BACKEND_DIRECTORY, PROJECT_DIRECTORY

EXPECTED_CLASSES = {0: "Drowning", 1: "Person out of water", 2: "Swimming"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def audit_dataset(dataset: Path) -> dict[str, object]:
    """Validate split folders, image/label pairs, rows, and class balance."""

    report: dict[str, object] = {"dataset": str(dataset), "splits": {}}
    total_classes: Counter[int] = Counter()
    for split in ("train", "valid", "test"):
        image_directory = dataset / split / "images"
        label_directory = dataset / split / "labels"
        if not image_directory.is_dir() or not label_directory.is_dir():
            raise ValueError(f"Dataset is missing {split}/images or {split}/labels.")
        images = {
            path.stem: path
            for path in image_directory.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        }
        labels = {path.stem: path for path in label_directory.glob("*.txt")}
        missing_labels = sorted(set(images) - set(labels))
        missing_images = sorted(set(labels) - set(images))
        if missing_labels or missing_images:
            raise ValueError(
                f"{split} has {len(missing_labels)} images without labels and "
                f"{len(missing_images)} labels without images."
            )
        class_counts: Counter[int] = Counter()
        box_count = 0
        for label_path in labels.values():
            for line_number, line in enumerate(
                label_path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                parts = line.split()
                if len(parts) != 5:
                    raise ValueError(f"Invalid YOLO row: {label_path}:{line_number}")
                class_id = int(parts[0])
                coordinates = [float(value) for value in parts[1:]]
                if class_id not in EXPECTED_CLASSES or any(
                    value < 0 or value > 1 for value in coordinates
                ):
                    raise ValueError(f"Invalid class/coordinate: {label_path}:{line_number}")
                class_counts[class_id] += 1
                total_classes[class_id] += 1
                box_count += 1
        report["splits"][split] = {
            "images": len(images),
            "labels": len(labels),
            "boxes": box_count,
            "classes": {
                EXPECTED_CLASSES[class_id]: class_counts[class_id]
                for class_id in EXPECTED_CLASSES
            },
        }
    report["total_classes"] = {
        EXPECTED_CLASSES[class_id]: total_classes[class_id]
        for class_id in EXPECTED_CLASSES
    }
    return report


def write_dataset_yaml(dataset: Path) -> Path:
    """Create an absolute-path YAML because the Roboflow export uses ../ paths."""

    training_directory = PROJECT_DIRECTORY / "storage" / "training"
    training_directory.mkdir(parents=True, exist_ok=True)
    path = training_directory / "aquatic-dataset.yaml"
    path.write_text(
        "\n".join(
            [
                f"path: {json.dumps(dataset.as_posix())}",
                "train: train/images",
                "val: valid/images",
                "test: test/images",
                "names:",
                '  0: "Drowning"',
                '  1: "Person out of water"',
                '  2: "Swimming"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path, help="Roboflow dataset root")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="", help="Empty=automatic, cpu, 0, or cuda:0")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--fraction", type=float, default=1.0)
    parser.add_argument("--name", default="aquaguard-aquatic")
    parser.add_argument(
        "--base-model",
        default=str(BACKEND_DIRECTORY / "yolo11n.pt"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIRECTORY / "models" / "aquaguard_aquatic_best.pt",
    )
    args = parser.parse_args()
    dataset = args.dataset.expanduser().resolve()
    if not dataset.is_dir():
        raise FileNotFoundError(f"Dataset folder was not found: {dataset}")
    if args.epochs < 1 or args.batch < 1:
        raise ValueError("Epochs and batch must be positive.")
    if not 0 < args.fraction <= 1:
        raise ValueError("Fraction must be greater than 0 and at most 1.")

    report = audit_dataset(dataset)
    print(json.dumps(report, indent=2))
    smallest_class = min(report["total_classes"].values())
    largest_class = max(report["total_classes"].values())
    if largest_class > smallest_class * 5:
        print("WARNING: The dataset is strongly class-imbalanced. Review per-class metrics.")
    data_yaml = write_dataset_yaml(dataset)
    print(f"corrected_data_yaml={data_yaml}")

    model = YOLO(args.base_model)
    training_arguments: dict[str, object] = {
        "data": str(data_yaml),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "workers": args.workers,
        "project": str(BACKEND_DIRECTORY / "runs" / "aquatic"),
        "name": args.name,
        "patience": 15,
        "pretrained": True,
        "plots": True,
        "save": True,
        "seed": 42,
        "exist_ok": False,
        "fraction": args.fraction,
    }
    if args.device:
        training_arguments["device"] = args.device
    result = model.train(**training_arguments)
    best_path = Path(model.trainer.best)
    if not best_path.is_file():
        raise RuntimeError("Training finished but best.pt was not created.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_path, args.output)

    best_model = YOLO(str(args.output))
    validation_arguments: dict[str, object] = {
        "data": str(data_yaml),
        "split": "test",
        "imgsz": args.imgsz,
        "batch": args.batch,
        "workers": args.workers,
        "plots": True,
    }
    if args.device:
        validation_arguments["device"] = args.device
    test_metrics = best_model.val(**validation_arguments)
    metrics = {
        key: float(value)
        for key, value in test_metrics.results_dict.items()
        if isinstance(value, (int, float)) or hasattr(value, "item")
    }
    metrics_path = args.output.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"trained_model={args.output}")
    print(f"test_metrics={metrics_path}")
    print(f"training_results={result.save_dir}")
    print("Restart AquaGuard so new sessions load the custom aquatic model.")


if __name__ == "__main__":
    main()
