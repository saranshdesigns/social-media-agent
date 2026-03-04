"use client";
import { useEffect, useState } from "react";
import { api, Overview } from "@/lib/api";
import { Play, Pause, Zap, Clock, ImageIcon, CalendarCheck, Upload, RefreshCw, Star } from "lucide-react";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">{label}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function ActionBtn({ onClick, icon: Icon, label, variant = "default" }: {
  onClick: () => void; icon: React.ElementType; label: string;
  variant?: "default" | "primary" | "danger" | "purple" | "amber";
}) {
  const styles = {
    default: "bg-gray-800 text-gray-200 hover:bg-gray-700",
    primary: "bg-brand-500 text-white hover:bg-brand-600",
    danger: "bg-red-900/60 text-red-300 hover:bg-red-900",
    purple: "bg-purple-900/60 text-purple-300 hover:bg-purple-900",
    amber: "bg-amber-900/60 text-amber-300 hover:bg-amber-900",
  };
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${styles[variant]}`}
    >
      <Icon size={14} strokeWidth={2} />
      {label}
    </button>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<{ text: string; type: "info" | "ok" } | null>(null);

  const load = () => {
    setLoading(true);
    api.overview().then(setData).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const notify = (text: string, type: "info" | "ok" = "ok") => {
    setMsg({ text, type });
    setTimeout(() => setMsg(null), 5000);
  };

  const handlePause = async () => { await api.pause(); notify("Automation paused."); load(); };
  const handleResume = async () => { await api.resume(); notify("Automation resumed."); load(); };
  const handleTrigger = async () => { const r = await api.trigger(); notify(r.message); };
  const handleBulk = async () => { const r = await api.triggerBulk(); notify(r.message, "info"); };
  const handleLatest = async () => { const r = await api.triggerLatest(); notify(r.message); };

  if (loading && !data) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-gray-500 text-sm">Loading...</div>
    </div>
  );

  if (!data) return <div className="text-red-400 text-sm">Failed to load data.</div>;

  return (
    <div className="max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Overview</h1>
          <p className="text-xs text-gray-500 mt-0.5">Portfolio automation status</p>
        </div>
        <div className="flex items-center gap-2">
          <ActionBtn onClick={load} icon={RefreshCw} label="Refresh" />
          <ActionBtn onClick={handleBulk} icon={Upload} label="Upload All" variant="purple" />
          <ActionBtn onClick={handleLatest} icon={Star} label="Post Latest" variant="amber" />
          <ActionBtn onClick={handleTrigger} icon={Zap} label="Post Now" variant="primary" />
          {data.automation_paused
            ? <ActionBtn onClick={handleResume} icon={Play} label="Resume" />
            : <ActionBtn onClick={handlePause} icon={Pause} label="Pause" variant="danger" />
          }
        </div>
      </div>

      {/* Message bar */}
      {msg && (
        <div className={`mb-5 px-4 py-3 rounded-lg text-sm border ${
          msg.type === "ok"
            ? "bg-green-900/20 border-green-800/40 text-green-300"
            : "bg-brand-500/10 border-brand-500/20 text-brand-500"
        }`}>
          {msg.text}
        </div>
      )}

      {/* Status badge */}
      <div className="flex items-center gap-2 mb-5">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
          data.automation_paused
            ? "bg-red-900/30 text-red-300 border border-red-800/40"
            : "bg-green-900/30 text-green-300 border border-green-800/40"
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${data.automation_paused ? "bg-red-400" : "bg-green-400"}`} />
          {data.automation_paused ? "Paused" : "Active"}
        </span>
        <span className="text-xs text-gray-600">Daily schedule: {data.schedule}</span>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <StatCard label="Total Posted" value={data.total_posted} />
        <StatCard label="Posted Today" value={data.posted_today} sub={`of ${data.max_posts_per_day} max`} />
        <StatCard label="Daily At" value={data.schedule} />
        <StatCard label="Max Per Day" value={data.max_posts_per_day} sub="per trigger" />
      </div>

      {/* Schedule info */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Schedule Info</span>
        </div>
        <div className="divide-y divide-gray-800">
          {[
            ["Last Run", data.last_run_at ? new Date(data.last_run_at).toLocaleString() : "Never"],
            ["Next Scheduled Run", data.next_run_at ? new Date(data.next_run_at).toLocaleString() : "—"],
          ].map(([label, value]) => (
            <div key={label} className="flex justify-between items-center px-5 py-3">
              <span className="text-sm text-gray-500">{label}</span>
              <span className="text-sm text-gray-200">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bulk upload info box */}
      <div className="mt-4 px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl">
        <p className="text-xs text-gray-500">
          <span className="text-purple-400 font-medium">Upload All</span> — posts every unposted image from Drive, mixed across categories (Packaging → Logo → Packaging…). No daily limit.
          Use for initial upload. Daily schedule also mixes categories automatically.
        </p>
      </div>
    </div>
  );
}
