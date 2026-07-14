import React, { useState } from "react";
import { AlertCircle, CheckCircle, Activity, Clock } from "lucide-react";
import { Incident } from "../../types/stadium";
import type { TimelineEvent } from "../../lib/types";
import { getPriorityStyle } from "../../lib/utils";

interface IncidentsListProps {
  incidents: Incident[];
  timeline: TimelineEvent[];
  onResolve?: (_id: string) => void;
}

export default function IncidentsList({
  incidents = [],
  timeline = [],
  onResolve,
}: IncidentsListProps) {
  const [activeTab, setActiveTab] = useState<"active" | "timeline">("active");

  const getTimelineEventStyle = (type: string) => {
    switch (type) {
      case "error":
      case "raised":
        return "border-danger bg-danger/5 text-danger";
      case "resolved":
        return "border-success bg-success/5 text-success";
      case "warning":
        return "border-warning bg-warning/5 text-warning";
      default:
        return "border-primary bg-primary/5 text-primary";
    }
  };

  return (
    <div className="glass rounded-2xl p-6 flex flex-col h-full overflow-hidden">
      {/* Tabs Header */}
      <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80 mb-4">
        <div className="flex gap-2 p-1 rounded-xl bg-zinc-900/60 border border-zinc-800">
          <button
            onClick={() => setActiveTab("active")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide uppercase transition-all duration-300 ${
              activeTab === "active"
                ? "bg-zinc-800 text-white shadow-md border border-zinc-700/50"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Active Incidents ({incidents.length})
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide uppercase transition-all duration-300 ${
              activeTab === "timeline"
                ? "bg-zinc-800 text-white shadow-md border border-zinc-700/50"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Audit Timeline ({timeline.length})
          </button>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-semibold tracking-wider text-primary uppercase">
          <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
          Live Center
        </div>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-y-auto pr-1">
        {activeTab === "active" ? (
          incidents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-sm font-light">
              <CheckCircle className="w-8 h-8 text-success mb-3 opacity-60" />
              All clear. No active incidents reported.
            </div>
          ) : (
            <div className="space-y-3">
              {incidents.map((inc) => (
                <div
                  key={inc.id}
                  className="p-4 rounded-xl border border-zinc-800/60 bg-zinc-900/25 hover:bg-zinc-900/50 transition-all duration-300 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 group"
                >
                  <div className="flex gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center border mt-0.5 shrink-0 ${getPriorityStyle(inc.priority)}`}>
                      <AlertCircle className="w-4.5 h-4.5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white group-hover:text-primary transition-colors duration-300">
                        {inc.title}
                      </h4>
                      <p className="text-xs text-zinc-400 font-light mt-1 max-w-md leading-relaxed">
                        {inc.description}
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-[10px] text-zinc-500 font-medium">
                        <span className="bg-zinc-800 px-2 py-0.5 rounded text-zinc-400 border border-zinc-700/60">
                          {inc.sector}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(inc.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {onResolve && inc.status !== "RESOLVED" && (
                    <button
                      onClick={() => onResolve(inc.id)}
                      className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 hover:border-success/50 hover:bg-success/5 hover:text-success text-xs font-semibold tracking-wide uppercase transition-all duration-300 self-end sm:self-center"
                    >
                      Resolve
                    </button>
                  )}
                </div>
              ))}
            </div>
          )
        ) : (
          timeline.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-sm font-light">
              <Activity className="w-8 h-8 text-primary mb-3 opacity-60 animate-pulse" />
              Waiting for telemetry flow...
            </div>
          ) : (
            <div className="relative border-l border-zinc-800 ml-3 pl-5 space-y-5 py-2">
              {timeline.slice(0, 40).map((evt) => (
                <div key={evt.id} className="relative group">
                  {/* Timeline dot */}
                  <span className={`absolute -left-[26px] top-1.5 w-3 h-3 rounded-full border-2 bg-background z-10 transition-all duration-300 group-hover:scale-125 ${
                    evt.type === 'error' || evt.type === 'raised'
                      ? 'border-danger'
                      : evt.type === 'resolved'
                      ? 'border-success'
                      : evt.type === 'warning'
                      ? 'border-warning'
                      : 'border-primary'
                  }`} />
                  
                  <div className="text-[10px] text-zinc-500 font-semibold tracking-wider uppercase mb-1">
                    {evt.time}
                  </div>
                  <div className={`p-3 rounded-xl border border-zinc-800/40 font-mono text-[11px] leading-relaxed transition-all duration-300 hover:border-zinc-700/50 ${getTimelineEventStyle(evt.type)}`}>
                    <div className="flex justify-between items-center mb-1 pb-1 border-b border-zinc-800/20 font-bold opacity-80">
                      <span>[{evt.topic.toUpperCase()}]</span>
                      <span className="text-[9px]">src: {evt.source}</span>
                    </div>
                    <span className="text-zinc-300">{evt.message}</span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
