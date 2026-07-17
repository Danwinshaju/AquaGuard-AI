# Temporal drowning model

The application never pretends an untrained model is accurate. Until `models/drowning_temporal.ts` exists, the temporal signal reports `not-trained` and AquaGuard continues with its explainable movement/pose rules.

Open `http://127.0.0.1:8000/model` and download the CSV template. Every `sequence_id` must contain at least 16 ordered frames. Replace the two illustrative sequences with many independently recorded sequences. Keep recordings from the same original video entirely on one side of your train/validation split when preparing a serious dataset, and include swimming, floating, playing, occlusion, reflections, empty pools, and staged emergency examples supervised by safety professionals. Never stage unsafe behavior in water.

The web page can upload the CSV, run training in the background, and display the validation metrics. Restart AquaGuard after successful training so new live sessions load the exported model.

From the `backend` directory, train and evaluate with:

```powershell
python .\ml\train_temporal_model.py .\ml\your-labelled-data.csv --epochs 30
```

The command prints accuracy, precision, recall, F1, and false-positive rate, then exports the TorchScript model used automatically by live and uploaded-video analysis after backend restart.
