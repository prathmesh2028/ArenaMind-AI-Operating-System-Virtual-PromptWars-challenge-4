"use client";

import React, { useEffect, useState } from "react";
import { Navigation, Locate } from "lucide-react";
import { getSectorCoords } from "../../lib/utils";

interface MapViewProps {
  activeTaskLocation?: string; // e.g. "Sector E" or "Sector B"
}

export default function MapView({ activeTaskLocation = "Sector E" }: MapViewProps) {
  // Volunteer GPS coordinates (stadium centered)
  const [lat, setLat] = useState(25.7749);
  const [lon, setLon] = useState(-80.1917);

  useEffect(() => {
    // Simulate slow GPS drift jitter
    const interval = setInterval(() => {
      setLat((l) => roundDecimal(l + (Math.random() - 0.5) * 0.0001));
      setLon((o) => roundDecimal(o + (Math.random() - 0.5) * 0.0001));
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const roundDecimal = (num: number) => {
    return Math.round(num * 1000000) / 1000000;
  };

  const destCoords = getSectorCoords(activeTaskLocation);

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-400">
          Tactical Concourse Routing
        </h2>
        <span className="text-[10px] text-zinc-500 font-light italic">
          GPS Live Tracking
        </span>
      </div>

      {/* Visual Stadium Radar/Map grid layout */}
      <div className="glass aspect-[4/3] w-full rounded-2xl border border-zinc-850 relative overflow-hidden flex items-center justify-center bg-zinc-950/40">
        
        {/* Draw a circular stadium boundary overlay outline */}
        <div className="absolute w-[85%] h-[80%] border-2 border-dashed border-zinc-800 rounded-[50px] flex items-center justify-center">
          {/* Inner pitch */}
          <div className="w-[45%] h-[40%] border border-zinc-850 bg-success/5 rounded-2xl flex items-center justify-center">
            <span className="text-[8px] font-black text-zinc-700 uppercase tracking-widest">Pitch Center</span>
          </div>
        </div>

        {/* Outer gate indicators */}
        <div className="absolute top-[8%] left-[22%] text-[9px] font-extrabold text-zinc-650">GATE 1</div>
        <div className="absolute top-[8%] right-[22%] text-[9px] font-extrabold text-zinc-650">GATE 2</div>
        <div className="absolute bottom-[8%] left-[22%] text-[9px] font-extrabold text-zinc-650">GATE 6</div>
        <div className="absolute bottom-[8%] right-[22%] text-[9px] font-extrabold text-zinc-650">GATE 5</div>

        {/* Sectors display text */}
        <div className="absolute top-[28%] left-[23%] text-[10px] font-bold text-zinc-500">Sector A</div>
        <div className="absolute top-[16%] left-[44%] text-[10px] font-bold text-zinc-500">Sector B</div>
        <div className="absolute top-[28%] right-[23%] text-[10px] font-bold text-zinc-500">Sector C</div>
        <div className="absolute bottom-[28%] right-[23%] text-[10px] font-bold text-zinc-500">Sector D</div>
        <div className="absolute bottom-[16%] left-[44%] text-[10px] font-bold text-zinc-500">Sector E</div>
        <div className="absolute bottom-[28%] left-[23%] text-[10px] font-bold text-zinc-500">Sector F</div>

        {/* Animated Directional Route Line from user center to task location */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          <line
            x1="50%"
            y1="50%"
            x2={destCoords.x}
            y2={destCoords.y}
            className="stroke-warning/60 stroke-[2] animate-dash"
          />
        </svg>

        {/* Volunteer GPS marker dot */}
        <div className="absolute top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] z-20 flex flex-col items-center">
          <div className="relative flex h-4 w-4 items-center justify-center">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/45 opacity-75"></span>
            <div className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary border border-white/60 shadow-[0_0_8px_#6366f1]" />
          </div>
          <span className="bg-primary border border-primary-dark/30 text-[7px] font-bold text-white px-1.5 py-0.5 rounded shadow mt-1">
            YOU
          </span>
        </div>

        {/* Active Task destination marker dot */}
        <div
          className="absolute z-20 flex flex-col items-center"
          style={{ top: destCoords.y, left: destCoords.x, transform: "translate(-50%, -50%)" }}
        >
          <div className="relative flex h-5 w-5 items-center justify-center">
            <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-warning/35 opacity-90 scale-125"></span>
            <Navigation className="relative w-4 h-4 text-warning fill-current transform rotate-45 shadow-[0_0_8px_#f59e0b]" />
          </div>
          <span className="bg-warning border border-warning-dark/30 text-[8px] font-black text-zinc-950 px-2 py-0.5 rounded shadow mt-1 uppercase tracking-wider">
            {activeTaskLocation || "Task"}
          </span>
        </div>
      </div>

      {/* GPS metadata card */}
      <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-900 grid grid-cols-2 gap-4 text-xs font-mono">
        <div>
          <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider block mb-0.5">Latitude Coords</span>
          <span className="text-white font-semibold flex items-center gap-1">
            <Locate className="w-3.5 h-3.5 text-primary" /> {lat.toFixed(6)} N
          </span>
        </div>
        <div>
          <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider block mb-0.5">Longitude Coords</span>
          <span className="text-white font-semibold flex items-center gap-1">
            <Locate className="w-3.5 h-3.5 text-primary" /> {Math.abs(lon).toFixed(6)} W
          </span>
        </div>
      </div>
    </div>
  );
}
