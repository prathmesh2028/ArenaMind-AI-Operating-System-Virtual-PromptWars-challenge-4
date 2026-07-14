/* eslint-disable no-unused-vars */
import React from "react";
import { Compass, Utensils, MessageSquare, AlertOctagon } from "lucide-react";

interface BottomNavProps {
  activeTab: string;
  setActiveTab: (_tab: string) => void;
  unreadCount?: number;
}

export default function BottomNav({ activeTab, setActiveTab, unreadCount = 0 }: BottomNavProps) {
  const tabs = [
    { id: "home", label: "Explore", icon: <Compass className="w-5.5 h-5.5" /> },
    { id: "food", label: "Food & Stalls", icon: <Utensils className="w-5.5 h-5.5" /> },
    { id: "assistant", label: "Assistant", icon: <MessageSquare className="w-5.5 h-5.5" /> },
    { id: "emergency", label: "SOS Help", icon: <AlertOctagon className="w-5.5 h-5.5" /> },
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
            {/* Active background pill */}
            <div className={`absolute inset-x-[-12px] top-[-4px] bottom-[18px] rounded-full transition-all duration-300 -z-10 ${
              isActive ? "bg-success/15 scale-100" : "bg-transparent scale-50 opacity-0"
            }`} />

            <div className={`transition-all duration-300 ${
              isActive ? "text-success scale-110" : "text-zinc-500 hover:text-zinc-350"
            }`}>
              {tab.icon}
            </div>

            <span className={`text-[10px] tracking-wider uppercase font-semibold transition-colors duration-300 ${
              isActive ? "text-success" : "text-zinc-500"
            }`}>
              {tab.label}
            </span>

            {/* Badge for notifications */}
            {tab.id === "assistant" && unreadCount > 0 && (
              <span className="absolute top-[-3px] right-[4px] w-4.5 h-4.5 bg-danger border border-zinc-950 rounded-full flex items-center justify-center text-[8px] font-extrabold text-white animate-pulse">
                {unreadCount}
              </span>
            )}

            {/* Accent colored top dot indicator */}
            {isActive && (
              <div className="absolute top-[-10px] w-1.5 h-1.5 bg-success rounded-full shadow-[0_0_8px_#10b981]" />
            )}
          </button>
        );
      })}
    </nav>
  );
}
