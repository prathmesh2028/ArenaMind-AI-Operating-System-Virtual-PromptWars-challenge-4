/* eslint-disable no-unused-vars */
import React from "react";
import { ClipboardList, AlertCircle, Map, Bot } from "lucide-react";

interface BottomNavProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  unreadCount?: number;
}

export default function BottomNav({ activeTab, setActiveTab, unreadCount = 0 }: BottomNavProps) {
  const tabs = [
    { id: "tasks", label: "Task Board", icon: <ClipboardList className="w-5.5 h-5.5" /> },
    { id: "report", label: "Report Issue", icon: <AlertCircle className="w-5.5 h-5.5" /> },
    { id: "map", label: "Active Map", icon: <Map className="w-5.5 h-5.5" /> },
    { id: "copilot", label: "AI Copilot", icon: <Bot className="w-5.5 h-5.5" /> },
  ];

  return (
    <nav className="border-t border-zinc-900 bg-zinc-950/95 backdrop-blur-md pb-4 pt-2.5 px-6 flex justify-around items-center w-full shrink-0 z-30 shadow-[0_-4px_20px_rgba(0,0,0,0.4)]">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            aria-label={tab.label}
            aria-selected={isActive}
            role="tab"
            className="flex flex-col items-center gap-1 relative py-1 focus:outline-none select-none cursor-pointer group"
          >
            {/* Active pill indicator */}
            <div className={`absolute inset-x-[-12px] top-[-4px] bottom-[18px] rounded-full transition-all duration-305 -z-10 ${
              isActive ? "bg-warning/15 scale-100" : "bg-transparent scale-50 opacity-0"
            }`} />

            <div className={`transition-all duration-300 ${
              isActive ? "text-warning scale-110" : "text-zinc-500 hover:text-zinc-350"
            }`}>
              {tab.icon}
            </div>

            <span className={`text-[10px] tracking-wider uppercase font-semibold transition-colors duration-300 ${
              isActive ? "text-warning" : "text-zinc-500"
            }`}>
              {tab.label}
            </span>

            {/* Notification Badge */}
            {tab.id === "copilot" && unreadCount > 0 && (
              <span className="absolute top-[-3px] right-[4px] w-4.5 h-4.5 bg-danger border border-zinc-950 rounded-full flex items-center justify-center text-[8px] font-extrabold text-white animate-pulse">
                {unreadCount}
              </span>
            )}

            {/* Top dot */}
            {isActive && (
              <div className="absolute top-[-10px] w-1.5 h-1.5 bg-warning rounded-full shadow-[0_0_8px_#f59e0b]" />
            )}
          </button>
        );
      })}
    </nav>
  );
}
