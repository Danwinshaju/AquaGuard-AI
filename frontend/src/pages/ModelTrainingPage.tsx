import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, BrainCircuit, CheckCircle2, Download, LoaderCircle, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchModelStatus, fetchTrainingJob, startModelTraining } from "../api/model";
import { AppShell } from "../components/AppShell";

export function ModelTrainingPage() {
  const queryClient = useQueryClient();
  const [dataset, setDataset] = useState<File | null>(null);
  const [epochs, setEpochs] = useState(30);
  const [jobId, setJobId] = useState<string | null>(null);
  const model = useQuery({ queryKey: ["model-status"], queryFn: fetchModelStatus });
  const job = useQuery({
    queryKey: ["training-job", jobId],
    queryFn: () => fetchTrainingJob(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      return state === "completed" || state === "failed" ? false : 2000;
    },
  });
  const training = useMutation({
    mutationFn: () => startModelTraining(dataset!, epochs),
    onSuccess: (createdJob) => setJobId(createdJob.id),
  });
  const active = training.isPending || job.data?.status === "queued" || job.data?.status === "training";

  useEffect(() => {
    if (job.data?.status === "completed") {
      void queryClient.invalidateQueries({ queryKey: ["model-status"] });
    }
  }, [job.data?.status, queryClient]);

  return (
    <AppShell>
      <div className="flex items-start gap-4">
        <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-violet-100 text-violet-700">
          <BrainCircuit size={30} />
        </span>
        <div>
          <h1 className="text-3xl font-black">Train temporal AI</h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Train the movement-sequence model with your own labelled pool observations. This
            improves behaviour classification; YOLO still performs person detection.
          </p>
        </div>
      </div>

      <section className="mt-6 rounded-2xl border border-amber-300 bg-amber-50 p-5 text-sm text-amber-950">
        <div className="flex gap-3">
          <AlertTriangle className="shrink-0 text-amber-700" size={22} />
          <p><strong>Safety requirement:</strong> use correctly labelled data from varied cameras, people, lighting and normal swimming. Always test on separate videos that were not used for training. A high score does not certify this system for lifesaving use.</p>
        </div>
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-black">1. Prepare the dataset</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Download the CSV example, keep its column names, and add many labelled sequences.
            The label must be <strong>0 for normal</strong> or <strong>1 for drowning-like behaviour</strong>.
          </p>
          <a className="mt-5 flex items-center justify-center gap-2 rounded-xl bg-slate-800 px-4 py-3 font-black text-white hover:bg-slate-900" href="/api/v1/model/dataset-template">
            <Download size={19} /> Download CSV template
          </a>
          <div className="mt-5 rounded-xl bg-slate-100 p-4 text-sm">
            <p className="font-black">Current model</p>
            {model.isLoading ? <p className="mt-2 text-slate-500">Checking…</p> : (
              <p className={`mt-2 font-bold ${model.data?.model_ready ? "text-emerald-700" : "text-amber-700"}`}>
                {model.data?.model_ready ? "Trained model file is ready" : "No trained temporal model yet"}
              </p>
            )}
            <p className="mt-1 break-all text-xs text-slate-500">Sequence length: {model.data?.sequence_length ?? 16} observations</p>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-black">2. Upload and train</h2>
          <label className="mt-5 block text-sm font-black text-slate-700">
            Labelled CSV file
            <input className="mt-2 block w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3" type="file" accept=".csv,text/csv" disabled={active} onChange={(event) => setDataset(event.target.files?.[0] ?? null)} />
          </label>
          <label className="mt-4 block text-sm font-black text-slate-700">
            Training epochs: {epochs}
            <input className="mt-2 w-full accent-violet-700" type="range" min="5" max="200" step="5" value={epochs} disabled={active} onChange={(event) => setEpochs(Number(event.target.value))} />
          </label>
          <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-violet-700 px-4 py-3 font-black text-white hover:bg-violet-800 disabled:cursor-not-allowed disabled:bg-slate-300" type="button" disabled={!dataset || active} onClick={() => training.mutate()}>
            {active ? <LoaderCircle className="animate-spin" size={20} /> : <Upload size={20} />}
            {active ? "Training in progress…" : "Start training"}
          </button>
          {training.isError && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm font-bold text-red-700">{training.error.message}</p>}
          {job.data && <TrainingResult status={job.data.status} metrics={job.data.metrics} output={job.data.output} error={job.data.error} />}
        </section>
      </div>

      <section className="mt-6 rounded-2xl border-2 border-ocean-300 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div><p className="text-xs font-black uppercase tracking-[0.16em] text-ocean-600">Your Roboflow object-detection dataset</p><h2 className="mt-2 text-2xl font-black">Train aquatic YOLO model</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">The audited dataset contains 12,365 images and three classes: Drowning, Person out of water, and Swimming. This model is different from the CSV temporal LSTM above. Training runs from PowerShell because it reads the full dataset folder.</p></div>
          <span className={`rounded-full px-4 py-2 text-sm font-black ${model.data?.aquatic_model_ready ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{model.data?.aquatic_model_ready ? "Aquatic model ready" : "Not trained yet"}</span>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-3"><div className="rounded-xl bg-slate-100 p-4"><p className="text-2xl font-black">10,140</p><p className="text-sm text-slate-600">Training images</p></div><div className="rounded-xl bg-slate-100 p-4"><p className="text-2xl font-black">1,478</p><p className="text-sm text-slate-600">Validation images</p></div><div className="rounded-xl bg-slate-100 p-4"><p className="text-2xl font-black">747</p><p className="text-sm text-slate-600">Untouched test images</p></div></div>
        <p className="mt-5 text-sm font-black text-slate-800">First run a one-epoch technical test with 5% of the data:</p>
        <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-cyan-100"><code>{`powershell -ExecutionPolicy Bypass -File .\\scripts\\train-aquatic-model.ps1 -Epochs 1 -Batch 4 -Fraction 0.05 -Device cpu`}</code></pre>
        <p className="mt-5 text-sm font-black text-slate-800">Simple demonstration training:</p>
        <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-cyan-100"><code>{`powershell -ExecutionPolicy Bypass -File .\\scripts\\train-aquatic-model.ps1 -Epochs 5 -Batch 4 -Fraction 0.10 -Device cpu`}</code></pre>
        <p className="mt-2 text-xs font-semibold text-amber-700">This creates a model for testing the workflow, but it is not sufficient for safety accuracy.</p>
        <p className="mt-4 text-sm text-slate-600">When the test succeeds, use 50 epochs for CPU training or follow the GPU command in the complete guide. Training may take many hours on CPU. Restart AquaGuard after training.</p>
        <a className="mt-4 inline-flex items-center gap-2 rounded-xl bg-ocean-600 px-5 py-3 font-black text-white hover:bg-ocean-700" href="/api/v1/documentation/aquatic-model-training"><Download size={19} /> Download aquatic training guide</a>
      </section>
    </AppShell>
  );
}

function TrainingResult({ status, metrics, output, error }: { status: string; metrics: Record<string, number>; output: string[]; error: string | null }) {
  const completed = status === "completed";
  return (
    <div className={`mt-5 rounded-xl border p-4 ${completed ? "border-emerald-300 bg-emerald-50" : status === "failed" ? "border-red-300 bg-red-50" : "border-violet-200 bg-violet-50"}`}>
      <div className="flex items-center gap-2 font-black uppercase tracking-wide">
        {completed ? <CheckCircle2 className="text-emerald-700" size={21} /> : <LoaderCircle className={status === "failed" ? "text-red-700" : "animate-spin text-violet-700"} size={21} />}
        {status}
      </div>
      {error && <p className="mt-3 text-sm font-bold text-red-800">{error}</p>}
      {Object.keys(metrics).length > 0 && <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">{Object.entries(metrics).map(([name, value]) => <div className="rounded-lg bg-white p-3" key={name}><p className="text-xs font-bold uppercase text-slate-500">{name.replaceAll("_", " ")}</p><p className="mt-1 text-xl font-black">{(value * 100).toFixed(1)}%</p></div>)}</div>}
      {completed && <p className="mt-4 text-sm font-bold text-emerald-900">Training is complete. Restart AquaGuard with npm start so new live sessions load this model.</p>}
      {output.length > 0 && <details className="mt-4"><summary className="cursor-pointer text-sm font-bold">Show training log</summary><pre className="mt-2 max-h-52 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">{output.join("\n")}</pre></details>}
    </div>
  );
}
