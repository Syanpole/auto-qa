type StationCardProps = {
  stationCode: string;
  status: "online" | "warning" | "offline";
  fps: number;
  queueDepth: number;
  passRate: number;
};

export default function StationCard(props: StationCardProps) {
  const color =
    props.status === "online" ? "bg-emerald-500" : props.status === "warning" ? "bg-amber-500" : "bg-rose-500";

  return (
    <article className="rounded-xl bg-white shadow p-5 border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg">{props.stationCode}</h3>
        <span className={`h-3 w-3 rounded-full ${color}`} />
      </div>
      <dl className="grid grid-cols-2 gap-y-2 text-sm">
        <dt className="text-slate-500">FPS</dt>
        <dd className="font-medium text-right">{props.fps}</dd>
        <dt className="text-slate-500">Queue</dt>
        <dd className="font-medium text-right">{props.queueDepth}</dd>
        <dt className="text-slate-500">Pass Rate</dt>
        <dd className="font-medium text-right">{props.passRate}%</dd>
      </dl>
    </article>
  );
}
