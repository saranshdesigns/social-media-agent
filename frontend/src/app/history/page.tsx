"use client";
import { useEffect, useState } from "react";
import { api, PostedImage } from "@/lib/api";
import { RefreshCw, Copy, Check, Layers } from "lucide-react";

const PLATFORMS = ["instagram", "facebook"] as const;

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "bg-pink-900/40 text-pink-300 border border-pink-800/40",
  facebook: "bg-blue-900/40 text-blue-300 border border-blue-800/40",
};

function PlatformBadge({ name, active }: { name: string; active: boolean }) {
  if (!active) return null;
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${PLATFORM_COLORS[name] || "bg-gray-800 text-gray-400"}`}>
      {name}
    </span>
  );
}

function CaptionCopy({ caption }: { caption: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={copy} className="shrink-0 p-1 text-gray-600 hover:text-gray-400 rounded">
      {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
    </button>
  );
}

export default function HistoryPage() {
  const [images, setImages] = useState<PostedImage[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.history(200).then(setImages).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-xl font-bold text-white">Posted History</h1>
          <p className="text-xs text-gray-500 mt-0.5">{images.length} images posted total</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-gray-300 rounded-lg text-sm hover:bg-gray-700"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>

      {loading && images.length === 0 ? (
        <div className="text-gray-500 text-sm">Loading...</div>
      ) : images.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-12 text-center">
          <div className="text-gray-500 text-sm">No posts yet.</div>
          <div className="text-gray-600 text-xs mt-1">Use "Bulk Upload" or "Post Now" from Overview.</div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {images.map((img, i) => {
            const isCarousel = img.file_name.includes(".");
            return (
              <div
                key={img.id}
                className={`flex gap-4 p-4 ${i < images.length - 1 ? "border-b border-gray-800" : ""}`}
              >
                {/* Thumbnail */}
                {img.cloudinary_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={img.cloudinary_url}
                    alt={img.file_name}
                    className="w-16 h-16 rounded-lg object-cover shrink-0 bg-gray-800"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-gray-800 shrink-0 flex items-center justify-center text-gray-600 text-xs">
                    —
                  </div>
                )}

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <p className="text-sm font-medium text-white truncate">{img.file_name}</p>
                        {isCarousel && (
                          <span className="shrink-0 flex items-center gap-1 px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded text-xs">
                            <Layers size={10} /> carousel
                          </span>
                        )}
                      </div>
                      {img.folder_path && (
                        <span className="text-xs text-gray-600">/{img.folder_path}</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-600 shrink-0">
                      {new Date(img.posted_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                    </span>
                  </div>

                  {/* Platform badges */}
                  <div className="flex gap-1.5 mt-2">
                    {PLATFORMS.map((p) => (
                      <PlatformBadge key={p} name={p} active={img[p] === 1} />
                    ))}
                  </div>

                  {/* Caption */}
                  {img.caption_used && (
                    <div className="flex items-start gap-1 mt-2">
                      <p className="text-xs text-gray-500 line-clamp-1 flex-1">{img.caption_used}</p>
                      <CaptionCopy caption={img.caption_used} />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
