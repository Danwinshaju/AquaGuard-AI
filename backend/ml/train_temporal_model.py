"""Train and evaluate the optional AquaGuard temporal drowning classifier."""

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

import torch
from torch import nn

FEATURE_COLUMNS = (
    "speed_normalized",
    "inactivity_normalized",
    "delta_y_normalized",
    "missing_normalized",
    "vertical_confidence",
    "irregular_arms_confidence",
    "head_hidden",
)


class TemporalLSTM(nn.Module):
    def __init__(self, feature_count: int = 7, hidden_size: int = 32) -> None:
        super().__init__()
        self.lstm = nn.LSTM(feature_count, hidden_size, batch_first=True)
        self.classifier = nn.Linear(hidden_size, 1)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        sequence_output, _ = self.lstm(features)
        return torch.sigmoid(self.classifier(sequence_output[:, -1, :]))


def load_sequences(
    path: Path,
    sequence_length: int,
) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
    grouped: dict[str, list[tuple[int, list[float], float]]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            grouped[row["sequence_id"]].append(
                (
                    int(row["frame"]),
                    [float(row[column]) for column in FEATURE_COLUMNS],
                    float(row["label"]),
                )
            )
    samples: list[list[list[float]]] = []
    labels: list[float] = []
    sample_groups: list[str] = []
    for sequence_id, rows in grouped.items():
        ordered = sorted(rows, key=lambda item: item[0])
        for end in range(sequence_length, len(ordered) + 1):
            window = ordered[end - sequence_length : end]
            samples.append([item[1] for item in window])
            labels.append(window[-1][2])
            sample_groups.append(sequence_id)
    if not samples:
        raise ValueError("Dataset has no complete temporal sequences.")
    return (
        torch.tensor(samples, dtype=torch.float32),
        torch.tensor(labels).reshape(-1, 1),
        sample_groups,
    )


def metrics(probabilities: torch.Tensor, labels: torch.Tensor) -> dict[str, float]:
    predictions = probabilities >= 0.5
    truth = labels >= 0.5
    true_positive = int((predictions & truth).sum())
    false_positive = int((predictions & ~truth).sum())
    false_negative = int((~predictions & truth).sum())
    true_negative = int((~predictions & ~truth).sum())
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    return {
        "accuracy": (true_positive + true_negative) / max(len(labels), 1),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / max(precision + recall, 1e-9),
        "false_positive_rate": false_positive / max(false_positive + true_negative, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, default=Path("models/drowning_temporal.ts"))
    parser.add_argument("--sequence-length", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=30)
    args = parser.parse_args()

    features, labels, sample_groups = load_sequences(args.dataset, args.sequence_length)
    group_ids = sorted(set(sample_groups))
    if len(group_ids) < 2:
        raise ValueError("Use at least two independent sequence IDs for train/validation.")
    random.Random(42).shuffle(group_ids)
    split = max(min(int(len(group_ids) * 0.8), len(group_ids) - 1), 1)
    train_groups = set(group_ids[:split])
    train_indices = [index for index, group in enumerate(sample_groups) if group in train_groups]
    validation_indices = [
        index for index, group in enumerate(sample_groups) if group not in train_groups
    ]
    model = TemporalLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_function = nn.BCELoss()
    for epoch in range(args.epochs):
        model.train()
        optimizer.zero_grad()
        probabilities = model(features[train_indices])
        loss = loss_function(probabilities, labels[train_indices])
        loss.backward()
        optimizer.step()
        if epoch == 0 or (epoch + 1) % 5 == 0:
            print(f"epoch={epoch + 1} loss={loss.item():.4f}")

    model.eval()
    with torch.inference_mode():
        results = metrics(model(features[validation_indices]), labels[validation_indices])
    for name, value in results.items():
        print(f"{name}={value:.3f}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.jit.script(model).save(str(args.output))
    print(f"saved={args.output}")


if __name__ == "__main__":
    main()
