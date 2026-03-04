"use client";
import { useEffect, useState } from "react";
import { api, PlatformLog } from "@/lib/api";
import { RefreshCw } from "lucide-react";
import clsx from "clsx";

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "text-pink-400",
  facebook: "text-blue-400",
};

type Filter = "all" | "success" | "failed";

export default function LogsPage() {
  const [logs, setLogs] = useState<PlatformLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");

  function load() {
    setLoading(true);
    api.logs(300).then(setLogs).finally(() => setLoading(false));
  }

  useEffect(load, []);

  const filtered = logs.filter((l) =>
    filter === "all" ? true : l.status === filter
  );

  const counts = {
    all: logs.length,
    success: logs.filter((l) => l.status === "success").length,
    failed: logs.filter((l) => l.status === "failed").length,
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-semibold text-white">Activity Logs</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            API results per post per platform — last 300 entries
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 hover:text-gray-200 text-xs font-medium disabled:opacity-50"
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {(["all", "success", "failed"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium capitalize",
              filter === f
                ? f === "failed"
                  ? "bg-red-900/50 text-red-300 border border-red-800"
                  : f === "success"
                  ? "bg-green-900/40 text-green-300 border border-green-800"
                  : "bg-brand-500 text-white"
                : "bg-gray-800 text-gray-400 hover:text-gray-200"
            )}
          >
            {f}
            <span
              className={clsx(
                "px-1.5 py-0.5 rounded text-[10px] font-bold",
                filter === f ? "bg-white/10" : "bg-gray-700 text-gray-400"
              )}
            >
              {counts[f]}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-500 text-sm py-8 text-center">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-gray-500 text-sm py-8 text-center bg-gray-900 border border-gray-800 rounded-xl">
          No logs found.
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-[11px] text-gray-500 uppercase tracking-wide">
                <th className="text-left px-4 py-3">Platform</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3 w-16">Attempt</th>
                <th className="text-left px-4 py-3">File ID</th>
                <th className="text-left px-4 py-3">Response / Error</th>
                <th className="text-left px-4 py-3 whitespace-nowrap">Logged At</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((log) => (
                <tr
                  key={log.id}
                  className="border-b border-gray-800/40 hover:bg-gray-800/20"
                >
                  <td className="px-4 py-2.5">
                    <span
                      className={clsx(
                        "font-medium capitalize",
                        PLATFORM_COLORS[log.platform] || "text-gray-300"
                      )}
                    >
                      {log.platform}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={clsx(
                        "px-2 py-0.5 rounded text-[11px] font-medium",
                        log.status === "success"
                          ? "bg-green-900/40 text-green-400"
                          : "bg-red-900/40 text-red-400"
                      )}
                    >
                      {log.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 text-center">
                    {log.attempt}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-gray-500 font-mono text-[11px]">
                      {log.drive_file_id.slice(0, 14)}…
                    </span>
                  </td>
                  <td className="px-4 py-2.5 max-w-xs">
                    <span
                      className="text-gray-400 text-xs block truncate"
                      title={log.response || ""}
                    >
                      {log.response || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                    {new Date(log.logged_at + "Z").toLocaleString("en-IN", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filtered.length > 0 && (
        <p className="text-xs text-gray-600 mt-3 text-right">
          Showing {filtered.length} of {logs.length} entries
        </p>
      )}
    </div>
  );
}
