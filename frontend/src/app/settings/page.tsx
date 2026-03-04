"use client";
import { useEffect, useState } from "react";
import { api, AppSettings } from "@/lib/api";
import { Clock, Timer, Layers, Bot, Repeat } from "lucide-react";

const ROWS: {
  key: keyof AppSettings;
  label: string;
  icon: React.FC<{ size?: number; className?: string }>;
  format: (v: AppSettings[keyof AppSettings]) => string;
}[] = [
  {
    key: "schedule_hour",
    label: "Daily Run Time (UTC)",
    icon: Clock,
    format: (v) => `${String(v).padStart(2, "0")}:00 UTC`,
  },
  {
    key: "schedule_minute",
    label: "Minute Offset",
    icon: Timer,
    format: (v) => `${v} min`,
  },
  {
    key: "post_interval_minutes",
    label: "Interval Between Posts",
    icon: Repeat,
    format: (v) => `${v} minutes`,
  },
  {
    key: "max_posts_per_day",
    label: "Max Posts Per Day",
    icon: Layers,
    format: (v) => `${v} posts`,
  },
  {
    key: "openai_model",
    label: "AI Caption Model",
    icon: Bot,
    format: (v) => String(v),
  },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.settings().then(setSettings).finally(() => setLoading(false));
  }, []);

  if (loading)
    return <div className="text-gray-500 text-sm">Loading...</div>;
  if (!settings)
    return <div className="text-red-400 text-sm">Failed to load settings.</div>;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-5">
        <h2 className="text-xl font-semibold text-white">Settings</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Current runtime configuration — read-only
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl divide-y divide-gray-800">
        {ROWS.map(({ key, label, icon: Icon, format }) => (
          <div key={key} className="flex items-center justify-between px-5 py-4">
            <div className="flex items-center gap-3">
              <Icon size={15} className="text-gray-500" />
              <span className="text-sm text-gray-400">{label}</span>
            </div>
            <span className="text-sm font-medium text-white font-mono">
              {format(settings[key])}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl">
        <p className="text-xs text-gray-500">
          To change these values, update your{" "}
          <code className="text-gray-400 bg-gray-800 px-1 py-0.5 rounded">.env</code>{" "}
          file and restart the backend server.
        </p>
      </div>
    </div>
  );
}
