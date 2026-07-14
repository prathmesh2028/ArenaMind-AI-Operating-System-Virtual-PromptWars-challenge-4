import React, { useEffect, useState } from "react";
import { CheckCircle2, Play, Check, Clock } from "lucide-react";
import { VolunteerTask } from "../../types/stadium";
import { getPriorityStyle, formatStopwatch } from "../../lib/utils";

interface TaskBoardProps {
  tasks: VolunteerTask[];
  onAccept: (_id: string) => void;
  onComplete: (_id: string) => void;
}

// Timer sub-component to run independent stopwatches for each accepted task
function ResponseTimer({ acceptedTime }: { acceptedTime: number }) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    // Start interval
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - acceptedTime) / 1000);
      setSeconds(elapsed >= 0 ? elapsed : 0);
    }, 1000);

    return () => clearInterval(interval);
  }, [acceptedTime]);

  return (
    <div className="flex items-center gap-1 bg-warning/10 text-warning border border-warning/20 px-2 py-0.5 rounded text-[10px] font-bold">
      <Clock className="w-3.5 h-3.5 animate-spin" style={{ animationDuration: "3s" }} />
      <span>Active: {formatStopwatch(seconds)}</span>
    </div>
  );
}

export default function TaskBoard({ tasks = [], onAccept, onComplete }: TaskBoardProps) {
  // Store acceptance timestamps for stopwatch timers locally in state
  const [acceptTimestamps, setAcceptTimestamps] = useState<Record<string, number>>({});

  const handleAcceptClick = (id: string) => {
    // Save acceptance time
    setAcceptTimestamps((prev) => ({
      ...prev,
      [id]: Date.now(),
    }));
    onAccept(id);
  };

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-400">
          Dispatched Tasks
        </h2>
        <span className="text-[10px] text-zinc-500 font-light italic">
          Prioritized Action Queue
        </span>
      </div>

      {tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-sm font-light glass border border-zinc-900 rounded-2xl">
          <CheckCircle2 className="w-8 h-8 text-success mb-3 opacity-60" />
          No tasks assigned. You are standby.
        </div>
      ) : (
        <div className="space-y-3.5">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="p-4 rounded-2xl border border-zinc-900 bg-zinc-950/20 hover:border-zinc-850 hover:bg-zinc-900/10 transition-all duration-300 relative overflow-hidden group"
            >
              {/* Left-edge priority stripe indicator */}
              <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${
                task.priority === "CRITICAL"
                  ? "bg-danger shadow-[0_0_8px_#f43f5e]"
                  : task.priority === "HIGH"
                  ? "bg-orange-500"
                  : task.priority === "MEDIUM"
                  ? "bg-warning"
                  : "bg-zinc-700"
              }`} />

              <div className="pl-1.5 space-y-3">
                <div className="flex justify-between items-center flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded text-[8px] font-black uppercase border tracking-wider ${getPriorityStyle(task.priority)}`}>
                      {task.priority}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-semibold uppercase">
                      ID: {task.id.substring(0, 8)}
                    </span>
                  </div>

                  {/* Render Stopwatch Timer for active ACCEPTED tasks */}
                  {task.status === "ACCEPTED" && (
                    <ResponseTimer acceptedTime={acceptTimestamps[task.id] || Date.now() - 30000} />
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white group-hover:text-warning transition-colors duration-300">
                    {task.title}
                  </h3>
                  <div className="flex items-center gap-1.5 text-[9px] text-zinc-500 font-semibold mt-1">
                    <span>Task Context: </span>
                    <span className="bg-zinc-900 text-zinc-400 border border-zinc-800 px-1.5 py-0.5 rounded font-bold uppercase">
                      Stadium Sector
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center pt-2.5 border-t border-zinc-900/60 gap-4">
                  <div className="text-[9px] text-zinc-500 font-light">
                    Assigned: {new Date(task.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>

                  {task.status === "PENDING" ? (
                    <button
                      onClick={() => handleAcceptClick(task.id)}
                      className="px-3.5 py-1.5 bg-warning hover:bg-warning-dark text-zinc-950 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all duration-300 flex items-center gap-1 cursor-pointer"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" /> Accept
                    </button>
                  ) : (
                    <button
                      onClick={() => onComplete(task.id)}
                      className="px-3.5 py-1.5 bg-success hover:bg-success-dark text-zinc-950 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-all duration-300 flex items-center gap-1 cursor-pointer"
                    >
                      <Check className="w-3.5 h-3.5 stroke-[3]" /> Complete
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
