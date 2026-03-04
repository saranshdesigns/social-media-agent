"use client";
import { useEffect, useState } from "react";
import { api, PlatformStatus } from "@/lib/api";
import { CheckCircle, XCircle, RefreshCw } from "lucide-react";

const PLATFORM_META: Record<string, { label: string; desc: string }> = {
  instagram: {
    label: "Instagram Business",
    desc: "Instagram Graph API — account ID + page access token",
  },
  facebook: {
    label: "Facebook Page",
    desc: "Facebook Graph API — page ID + page access token",
  },
  google_drive: {
    label: "Google Drive",
    desc: "Service account with read access to portfolio folder",
  },
  openai: {
    label: "OpenAI API",
    desc: "GPT-4o-mini for AI caption generation",
  },
  server_url: {
    label: "Image Hosting Server",
    desc: "Public server URL for serving temp images to Meta APIs",
  },
};

export default function PlatformsPage() {
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api.platforms().then(setStatus).finally(() => setLoading(false));
  }

  useEffect(load, []);

  const entries = status
    ? (Object.entries(status) as [keyof PlatformStatus, boolean][])
    : [];
  const allOk = entries.length > 0 && entries.every(([, v]) => v);
  const missingCount = entries.filter(([, v]) => !v).length;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-semibold text-white">Connections</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Checks if credentials are configured — not a live ping
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

      {/* Overall status banner */}
      {status && (
        <div
          className={`mb-4 px-4 py-3 rounded-xl border text-sm font-medium flex items-center gap-2 ${
            allOk
              ? "bg-green-900/20 border-green-800 text-green-400"
              : "bg-yellow-900/20 border-yellow-800 text-yellow-400"
          }`}
        >
          {allOk ? (
            <>
              <CheckCircle size={15} />
              All platforms configured — system ready
            </>
          ) : (
            <>
              <XCircle size={15} />
              {missingCount} platform{missingCount > 1 ? "s" : ""} missing credentials
            </>
          )}
        </div>
      )}

      {loading ? (
        <div className="text-gray-500 text-sm py-8 text-center bg-gray-900 border border-gray-800 rounded-xl">
          Loading...
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl divide-y divide-gray-800">
          {entries.map(([key, connected]) => (
            <div key={key} className="flex items-start justify-between px-5 py-4">
              <div>
                <p className="text-sm font-medium text-gray-200">
                  {PLATFORM_META[key]?.label || key}
                </p>
                <p className="text-xs text-gray-600 mt-0.5">
                  {PLATFORM_META[key]?.desc}
                </p>
              </div>
              <div className="flex items-center gap-1.5 mt-0.5 shrink-0 ml-4">
                {connected ? (
                  <>
                    <CheckCircle size={15} className="text-green-400" />
                    <span className="text-xs text-green-400 font-medium">Configured</span>
                  </>
                ) : (
                  <>
                    <XCircle size={15} className="text-red-400" />
                    <span className="text-xs text-red-400 font-medium">Missing</span>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-600 mt-4">
        Update credentials in{" "}
        <code className="text-gray-400 bg-gray-800 px-1 py-0.5 rounded">.env</code>{" "}
        and restart the backend to apply changes.
      </p>
    </div>
  );
}
