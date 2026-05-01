import StationCard from "../components/StationCard";

const stations = [
  { stationCode: "QA-01", status: "online" as const, fps: 23, queueDepth: 1, passRate: 97.1 },
  { stationCode: "QA-02", status: "online" as const, fps: 22, queueDepth: 2, passRate: 96.4 },
  { stationCode: "QA-03", status: "warning" as const, fps: 18, queueDepth: 5, passRate: 95.8 },
  { stationCode: "QA-04", status: "online" as const, fps: 24, queueDepth: 1, passRate: 97.7 },
];

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl bg-white p-5 shadow border border-slate-200">
          <p className="text-sm text-slate-500">Detection Accuracy</p>
          <p className="text-3xl font-extrabold text-steel">96.8%</p>
        </article>
        <article className="rounded-2xl bg-white p-5 shadow border border-slate-200">
          <p className="text-sm text-slate-500">False Reject Rate</p>
          <p className="text-3xl font-extrabold text-copper">2.4%</p>
        </article>
        <article className="rounded-2xl bg-white p-5 shadow border border-slate-200">
          <p className="text-sm text-slate-500">Average Inference Latency</p>
          <p className="text-3xl font-extrabold text-mint">132 ms</p>
        </article>
      </div>

      <div>
        <h2 className="text-xl font-bold mb-3">QA Station Live Status</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stations.map((station) => (
            <StationCard key={station.stationCode} {...station} />
          ))}
        </div>
      </div>

      <article className="rounded-2xl bg-gradient-to-r from-steel to-slate-700 text-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold">Threshold Control Guidance</h3>
        <p className="mt-2 text-sm opacity-90">
          Recommended initial confidence threshold is 0.85. Tune per product and station using pilot validation data.
        </p>
      </article>
    </section>
  );
}
