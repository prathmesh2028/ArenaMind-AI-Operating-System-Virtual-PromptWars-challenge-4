import React from "react";
import { AlertCircle, ShieldAlert, Cpu, HeartPulse, ClipboardList, CheckCircle2 } from "lucide-react";

interface ReplayOverlayProps {
  currentFrameTime: string;
  activeIncident: { title: string; description: string; priority: string; sector: string } | null;
  activeDecision: { action: string; impact: string; target: string; eta: number } | null;
  logs: Array<{ timestamp: string; type: string; message: string }>;
}

export default function ReplayOverlay({
  currentFrameTime = "",
  activeIncident = null,
  activeDecision = null,
  logs = [],
}: ReplayOverlayProps) {
  
  const getPriorityBadge = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case "CRITICAL":
        return "bg-danger/10 border-danger/35 text-danger";
      case "HIGH":
        return "bg-orange-500/10 border-orange-500/35 text-orange-400";
      default:
        return "bg-warning/10 border-warning/35 text-warning";
    }
  };

  return (
    <div className="space-y-4">
      {/* Active Incident details */}
      {activeIncident ? (
        <div className="glass p-5 rounded-2xl border border-danger/25 bg-danger/5 space-y-3.5 relative overflow-hidden animate-slideLeft">
          <div className="absolute top-[-10px] right-[-10px] w-24 h-24 bg-danger/5 rounded-full blur-xl" />
          <div className="flex justify-between items-center">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-danger bg-danger/10 px-2 py-0.5 rounded border border-danger/25 flex items-center gap-1 animate-pulse">
              <ShieldAlert className="w-3.5 h-3.5" /> Incident Registered
            </span>
            <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded border tracking-wider ${getPriorityBadge(activeIncident.priority)}`}>
              {activeIncident.priority}
            </span>
          </div>
          <div>
            <h4 className="text-xs font-black text-white">{activeIncident.title}</h4>
            <p className="text-[10px] text-zinc-400 font-light mt-1 leading-relaxed">
              {activeIncident.description}
            </p>
          </div>
          <div className="text-[9px] text-zinc-500 font-semibold pt-2 border-t border-zinc-900/60">
            Location: {activeIncident.sector} &bull; Timestamp: {currentFrameTime}
          </div>
        </div>
      ) : (
        <div className="glass p-5 rounded-2xl border border-zinc-850 flex flex-col items-center justify-center text-center h-28 text-zinc-500 text-[10px] font-light">
          <CheckCircle2 className="w-6 h-6 text-success opacity-60 mb-2" />
          Concourses Operating Nominal. No active incidents.
        </div>
      )}

      {/* Rules engine mitigation decision card */}
      {activeDecision && (
        <div className="glass p-5 rounded-2xl border border-warning/25 bg-warning/5 space-y-3.5 relative overflow-hidden animate-slideLeft">
          <div className="absolute top-[-10px] right-[-10px] w-24 h-24 bg-warning/5 rounded-full blur-xl" />
          <div className="flex justify-between items-center">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-warning bg-warning/10 px-2 py-0.5 rounded border border-warning/25 flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5" /> AI Mitigation Plan
            </span>
            <span className="text-[8px] font-extrabold text-zinc-400 uppercase tracking-widest">Rules Engine</span>
          </div>
          <div>
            <h4 className="text-xs font-black text-white">{activeDecision.action}</h4>
            <p className="text-[10px] text-zinc-400 font-light mt-1 leading-relaxed">
              <strong>Impact target:</strong> {activeDecision.impact}
            </p>
          </div>
          <div className="text-[9px] text-zinc-500 font-semibold pt-2 border-t border-zinc-900/60">
            Dispatch targets: {activeDecision.target} &bull; ETA: {activeDecision.eta} mins
          </div>
        </div>
      )}

      {/* Replay event log console */}
      <div className="glass p-5 rounded-2xl border border-zinc-850 flex flex-col h-[200px]">
        <h4 className="text-[10px] font-extrabold text-zinc-400 uppercase tracking-wider pb-2 border-b border-zinc-900 flex items-center gap-1.5 shrink-0">
          <ClipboardList className="w-4 h-4 text-danger" />
          Event Replay Console
        </h4>
        <div className="flex-1 overflow-y-auto space-y-2 mt-3 pr-1 text-[10px] font-mono leading-relaxed">
          {logs.slice(0, 15).map((log, idx) => (
            <div key={idx} className="p-2 rounded bg-zinc-950/40 border border-zinc-900/60 text-zinc-400 flex gap-2">
              <span className="text-danger shrink-0 font-bold">[{log.type}]</span>
              <span className="text-zinc-350">{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-center text-zinc-600 text-[10px] font-light mt-8">
              Awaiting session timeline playback...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
