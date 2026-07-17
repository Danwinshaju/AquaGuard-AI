# Train AquaGuard with the Swimming and Drowning Dataset

Author and developer: Danwin Shaju  
Email: [danwin212@gmail.com](mailto:danwin212@gmail.com)  
GitHub: [github.com/Danwinshaju](https://github.com/Danwinshaju)  
LinkedIn: [linkedin.com/in/danwin-shaju](https://www.linkedin.com/in/danwin-shaju/)  
Copyright: © 2026 Danwin Shaju. All rights reserved.

Dataset: `Swimming and Drowning Detection.v1i.yolov12`  
Classes: Drowning, Person out of water, Swimming  
Images: 12,365  
License reported by the export: CC BY 4.0

## Dataset audit

| Split | Images | Drowning boxes | Out-of-water boxes | Swimming boxes |
|---|---:|---:|---:|---:|
| Train | 10,140 | 10,867 | 616 | 7,269 |
| Validation | 1,478 | 1,577 | 98 | 1,073 |
| Test | 747 | 787 | 71 | 663 |

All 12,365 images have matching label files, and all 23,021 audited annotation rows use valid class IDs and YOLO coordinates. The out-of-water class is strongly under-represented, so review per-class precision and recall rather than only overall mAP.

The dataset contains closely spaced video frames and pre-generated augmentations. Similar source scenes may occur across splits, so reported test metrics can be optimistic. For a stronger evaluation, create an additional test set from entirely different source videos, pools, people, and camera positions.

The exported `data.yaml` contains `../train`-style paths. The AquaGuard training script creates a corrected absolute-path YAML automatically.

## Quick pipeline test

Use one epoch with 5% of the training split to confirm the complete pipeline works:

```powershell
cd "C:\Users\ELCOT\OneDrive - ELCOT\Documents\AI Drowning Detection"
powershell -ExecutionPolicy Bypass -File .\scripts\train-aquatic-model.ps1 -Epochs 1 -Batch 4 -Fraction 0.05 -Device cpu
```

This is only a technical test and does not create a validated model.

## Simple demonstration training

For a simple model that demonstrates the complete training and application workflow, use five epochs and 10% of the training data:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\train-aquatic-model.ps1 -Epochs 5 -Batch 4 -Fraction 0.10 -Device cpu
```

This creates `backend/models/aquaguard_aquatic_best.pt`, but it is not sufficient for real safety accuracy or performance claims.

## Full training

CPU training may take many hours or days:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\train-aquatic-model.ps1 -Epochs 50 -Batch 8 -Device cpu
```

For a correctly installed NVIDIA CUDA environment, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\train-aquatic-model.ps1 -Epochs 80 -Batch 16 -Device 0
```

If GPU memory is insufficient, reduce `-Batch` to 8, 4, or 2.

## Outputs

- Final model: `backend/models/aquaguard_aquatic_best.pt`
- Test metrics: `backend/models/aquaguard_aquatic_best.metrics.json`
- Training graphs and checkpoints: `backend/runs/aquatic/`

After training, restart AquaGuard with `npm start`. The model runs periodically alongside normal person tracking. A confident `Drowning` appearance becomes an explainable risk contribution; it does not bypass smoothing, temporal persistence, other signals, or human verification.

Confirm that `MOCK_AI=false` in `backend/.env` before evaluating the trained model with real video.

## Responsible evaluation

- Keep the provided test split unused during training.
- Review confusion matrices and per-class precision/recall.
- Check false positives on normal swimming, floating, splashing, reflections, empty water, and people beside the pool.
- Check missed detections across camera distance, glare, lighting, occlusion, and different pools.
- Do not claim that image mAP proves real-time drowning detection accuracy.
- Never stage unsafe behaviour to create new data.
