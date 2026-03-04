"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ImageIcon, ScrollText, Settings, Plug } from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/history", label: "Posted History", icon: ImageIcon },
  { href: "/logs", label: "Activity Logs", icon: ScrollText },
  { href: "/platforms", label: "Connections", icon: Plug },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="px-5 py-5 border-b border-gray-800">
        <div className="text-xs font-bold text-brand-500 uppercase tracking-widest mb-0.5">
          Social Agent
        </div>
        <div className="text-xs text-gray-500">Portfolio Automation</div>
      </div>

      <nav className="flex flex-col gap-0.5 p-3 flex-1">
        {NAV.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium",
              path === href
                ? "bg-brand-500 text-white"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            )}
          >
            <Icon size={15} strokeWidth={1.8} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-gray-800">
        <div className="text-xs text-gray-600">SaranshDesigns</div>
      </div>
    </aside>
  );
}
