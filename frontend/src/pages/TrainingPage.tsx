export default function TrainingPage() {
  return (
    <section className="grid gap-4 md:grid-cols-2">
      <article className="rounded-2xl bg-white shadow border border-slate-200 p-5">
        <h2 className="text-xl font-bold mb-2">Dataset Versioning</h2>
        <p className="text-sm text-slate-600 mb-4">
          Manage curated production defect datasets for retraining and model drift control.
        </p>
        <ul className="text-sm space-y-2">
          <li>dataset_ic_defects:v2026.05.01</li>
          <li>dataset_ic_defects:v2026.04.15</li>
          <li>dataset_mesa_defects:v2026.04.10</li>
        </ul>
      </article>

      <article className="rounded-2xl bg-white shadow border border-slate-200 p-5">
        <h2 className="text-xl font-bold mb-2">Training Jobs</h2>
        <p className="text-sm text-slate-600 mb-4">
          Queue model fine-tuning jobs with baseline ESMD-YOLOv26n or RT-DETR.
        </p>
        <div className="text-sm space-y-2">
          <p>JOB-20260501-001: running</p>
          <p>JOB-20260428-002: completed</p>
          <p>JOB-20260421-003: completed</p>
        </div>
      </article>
    </section>
  );
}
