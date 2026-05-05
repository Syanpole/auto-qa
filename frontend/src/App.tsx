import { NavLink, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import DefectHistoryPage from "./pages/DefectHistoryPage";
import TrainingPage from "./pages/TrainingPage";
import LiveScreenPage from "./pages/LiveScreenPage";
import RealTimeDetectionPage from "./pages/RealTimeDetectionPage";
import AdminModelManagementPage from "./pages/AdminModelManagementPage";

export default function App() {
  return (
    <div className="min-h-screen bg-fog text-slate-900 font-body">
      <header className="bg-steel text-white shadow-lg">
        <div className="mx-auto max-w-7xl px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-headline font-extrabold tracking-tight">Teamglac AUTO QA</h1>
            <p className="text-sm opacity-80">Semiconductor IC Defect Intelligence Platform</p>
          </div>
          <nav className="flex gap-2 text-sm flex-wrap">
            <NavLink to="/" className="px-3 py-2 rounded bg-white/10 hover:bg-white/20">Dashboard</NavLink>
            <NavLink to="/detection" className="px-3 py-2 rounded bg-white/10 hover:bg-white/20">Detection</NavLink>
            <NavLink to="/history" className="px-3 py-2 rounded bg-white/10 hover:bg-white/20">Defect History</NavLink>
            <NavLink to="/live" className="px-3 py-2 rounded bg-white/10 hover:bg-white/20">Live Screen</NavLink>
            <NavLink to="/training" className="px-3 py-2 rounded bg-white/10 hover:bg-white/20">Training</NavLink>
            <NavLink to="/admin/models" className="px-3 py-2 rounded bg-white/10 hover:bg-white/20">🔧 Models</NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/detection" element={<RealTimeDetectionPage />} />
          <Route path="/live" element={<LiveScreenPage />} />
          <Route path="/history" element={<DefectHistoryPage />} />
          <Route path="/training" element={<TrainingPage />} />
          <Route path="/admin/models" element={<AdminModelManagementPage />} />
        </Routes>
      </main>
    </div>
  );
}
