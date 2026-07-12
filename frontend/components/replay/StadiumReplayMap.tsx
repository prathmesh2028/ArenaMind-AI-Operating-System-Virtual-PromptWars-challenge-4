import { AlertTriangle, Compass } from "lucide-react";

interface StadiumReplayMapProps {
  sectorDensities: Record<string, number>;
  volunteerPos: { x: number; y: number };
  activeIncidentSector: string | null;
}

export default function StadiumReplayMap({
  sectorDensities = {},
  volunteerPos = { x: 50, y: 50 },
  activeIncidentSector = null,
}: StadiumReplayMapProps) {
  
  // Grid coordinates representing stadium sectors
  const sectorPositions: Record<string, { x: string; y: string }> = {
    "Sector A": { x: "25%", y: "30%" },
    "Sector B": { x: "50%", y: "20%" },
    "Sector C": { x: "75%", y: "30%" },
    "Sector D": { x: "75%", y: "70%" },
    "Sector E": { x: "50%", y: "80%" },
    "Sector F": { x: "25%", y: "70%" },
  };

  return (
    <div className="glass p-5 rounded-2xl border border-zinc-850 space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-zinc-900">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
          <Compass className="w-4.5 h-4.5 text-danger" />
          Spatial Simulation Overlay
        </h3>
        <span className="text-[10px] text-zinc-500 font-light font-mono">Telemetry Replay</span>
      </div>

      <div className="aspect-[4/3] w-full rounded-xl bg-zinc-950/40 relative overflow-hidden flex items-center justify-center border border-zinc-900/60">
        
        {/* Draw a circular stadium boundary overlay outline */}
        <div className="absolute w-[85%] h-[80%] border-2 border-dashed border-zinc-900 rounded-[50px] flex items-center justify-center">
          {/* Inner pitch */}
          <div className="w-[45%] h-[40%] border border-zinc-900 bg-success/5 rounded-2xl flex items-center justify-center">
            <span className="text-[8px] font-black text-zinc-800 uppercase tracking-widest">Pitch Field</span>
          </div>
        </div>

        {/* Sectors */}
        {Object.entries(sectorPositions).map(([name, coords]) => {
          const density = sectorDensities[name] || 50;
          const isIncident = activeIncidentSector === name;

          return (
            <div
              key={name}
              className="absolute z-10 flex flex-col items-center group cursor-pointer transition-all duration-300"
              style={{ top: coords.y, left: coords.x, transform: "translate(-50%, -50%)" }}
            >
              {/* Sector indicator box */}
              <div className={`px-2.5 py-1.5 rounded-xl border flex flex-col items-center gap-0.5 text-center min-w-[70px] backdrop-blur-sm transition-all duration-300 ${
                isIncident ? "bg-danger/20 border-danger animate-pulse shadow-[0_0_12px_#f43f5e]" : "bg-zinc-950/60 border-zinc-850"
              }`}>
                <span className="text-[9px] font-extrabold text-white uppercase tracking-wider">{name.replace("Sector ", "Sec ")}</span>
                
                {/* Micro heat status circle */}
                <div className="flex items-center gap-1 mt-0.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    density >= 90 ? "bg-danger animate-ping" : density >= 75 ? "bg-warning" : "bg-success"
                  }`} />
                  <span className="text-[9px] font-bold text-zinc-400 font-mono">{density}%</span>
                </div>
              </div>

              {/* Sector detail hover tooltip */}
              {isIncident && (
                <div className="absolute top-[-38px] bg-danger text-white border border-danger-dark font-extrabold text-[8px] px-2 py-0.5 rounded shadow-[0_2px_8px_rgba(0,0,0,0.5)] uppercase tracking-wider flex items-center gap-1 z-30 animate-bounce">
                  <AlertTriangle className="w-3 h-3 fill-current" /> SOS ALERT
                </div>
              )}
            </div>
          );
        })}

        {/* Dispatch Route Line */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          {/* Path from user center to Gate 2 */}
          <line
            x1="50%"
            y1="50%"
            x2="75%"
            y2="70%"
            className="stroke-warning/60 stroke-[2] animate-dash"
          />
        </svg>

        {/* Animated Volunteer dot moving */}
        <div
          className="absolute z-20 transition-all duration-300 flex flex-col items-center"
          style={{ top: `${volunteerPos.y}%`, left: `${volunteerPos.x}%`, transform: "translate(-50%, -50%)" }}
        >
          <div className="relative flex h-4.5 w-4.5 items-center justify-center">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-warning/30 opacity-75"></span>
            <div className="relative inline-flex rounded-full h-2.5 w-2.5 bg-warning border border-zinc-950 shadow-[0_0_8px_#f59e0b]" />
          </div>
          <span className="bg-warning text-zinc-950 text-[7px] font-black px-1 rounded shadow mt-0.5 uppercase tracking-wide">
            Juan (Vol)
          </span>
        </div>
      </div>

      {/* Live legend bar */}
      <div className="flex justify-between items-center gap-4 text-[9px] font-semibold text-zinc-500 pt-1 border-t border-zinc-900">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-success/20 border border-success" />
          <span>Normal Density</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-warning/20 border border-warning" />
          <span>Warning Density (75%+)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-danger/20 border border-danger animate-pulse" />
          <span>Critical Congestion (90%+)</span>
        </div>
      </div>
    </div>
  );
}
