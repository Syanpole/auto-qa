const rows = [
  { ts: "2026-05-01 07:20:16", station: "QA-01", lot: "L240501-A", defect: "scratch", conf: 0.93, result: "fail" },
  { ts: "2026-05-01 07:20:43", station: "QA-03", lot: "L240501-B", defect: "crack", conf: 0.91, result: "fail" },
  { ts: "2026-05-01 07:21:01", station: "QA-02", lot: "L240501-A", defect: "surface_damage", conf: 0.88, result: "review" },
];

export default function DefectHistoryPage() {
  return (
    <section className="rounded-2xl bg-white shadow border border-slate-200 p-5 overflow-auto">
      <h2 className="text-xl font-bold mb-4">Defect History</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b">
            <th className="py-2">Timestamp</th>
            <th>Station</th>
            <th>Lot</th>
            <th>Defect</th>
            <th>Confidence</th>
            <th>Result</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr className="border-b" key={`${row.ts}-${row.station}`}>
              <td className="py-2">{row.ts}</td>
              <td>{row.station}</td>
              <td>{row.lot}</td>
              <td>{row.defect}</td>
              <td>{row.conf}</td>
              <td className="font-semibold uppercase">{row.result}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
