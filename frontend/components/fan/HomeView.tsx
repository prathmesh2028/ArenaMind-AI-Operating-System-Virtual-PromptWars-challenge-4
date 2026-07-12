"use client";

import React, { useState } from "react";
import { QrCode, MapPin, Bus, Car, Check } from "lucide-react";

interface ParkingItem {
  name: string;
  available_spots: number;
  status: string;
  occupancy_pct: number;
}

interface TransportItem {
  route: string;
  type: string;
  status: string;
  current_stop: string;
  seats_available: number;
}

interface HomeViewProps {
  parkingLots: ParkingItem[];
  transitVehicles: TransportItem[];
  _sectors: Array<{ sector: string; density_pct: number; wait_time_seconds: number }>;
}

export default function HomeView({ parkingLots = [], transitVehicles = [], _sectors = [] }: HomeViewProps) {
  const [section, setSection] = useState("");
  const [row, setRow] = useState("");
  const [seat, setSeat] = useState("");
  const [seatLocation, setSeatLocation] = useState<any | null>(null);

  const handleLocateSeat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!section) return;

    // Simulated seat mapping logic
    const secNum = parseInt(section) || 100;
    let gate = "Gate 1";
    let zone = "North Concourse";
    let path = "Take escalator 3 to Level 1, head right past Concession Section D.";

    if (secNum >= 120 && secNum < 200) {
      gate = "Gate 2";
      zone = "East Concourse";
      path = "Enter via Gate 2, pass turnstile lines, take elevator B to Row level.";
    } else if (secNum >= 200) {
      gate = "Gate 5";
      zone = "South Concourse";
      path = "Enter via Gate 5, elevator E to level 2, turn right.";
    }

    setSeatLocation({
      section,
      row: row || "F",
      seat: seat || "12",
      gate,
      zone,
      directions: path,
    });
  };

  // Find the parking lot with the most free spots
  const bestParking = parkingLots.reduce(
    (best, current) => (current.available_spots > (best?.available_spots || 0) ? current : best),
    null as ParkingItem | null
  );

  return (
    <div className="space-y-6 pb-6">
      {/* Premium Ticket Card with QR Code */}
      <div className="bg-gradient-to-br from-success-dark to-success/40 p-5 rounded-2xl relative overflow-hidden shadow-lg border border-success/35">
        <div className="absolute right-[-20px] bottom-[-25px] w-36 h-36 bg-white/5 rounded-full blur-2xl" />
        <div className="flex justify-between items-start mb-4">
          <div>
            <span className="text-[9px] bg-white/20 text-white px-2 py-0.5 rounded font-extrabold tracking-wider uppercase">
              FIFA World Cup 2026
            </span>
            <h2 className="text-lg font-black text-white mt-1.5 leading-tight">
              Argentina vs France
            </h2>
            <p className="text-[10px] text-white/80 font-light mt-0.5">
              Hard Rock Stadium &bull; Kickoff 20:00 EST
            </p>
          </div>
          <div className="p-1 bg-white rounded-lg shadow-md shrink-0">
            <QrCode className="w-10 h-10 text-zinc-950" />
          </div>
        </div>

        <div className="flex justify-between items-center pt-3 border-t border-white/20 text-white font-mono text-[10px]">
          <div>
            <div className="opacity-70 text-[9px]">GATE</div>
            <div className="font-bold text-sm">GATE 2</div>
          </div>
          <div>
            <div className="opacity-70 text-[9px]">SECTION</div>
            <div className="font-bold text-sm">{section || "114"}</div>
          </div>
          <div>
            <div className="opacity-70 text-[9px]">ROW</div>
            <div className="font-bold text-sm">{row || "F"}</div>
          </div>
          <div>
            <div className="opacity-70 text-[9px]">SEAT</div>
            <div className="font-bold text-sm">{seat || "12"}</div>
          </div>
        </div>
      </div>

      {/* Seat Finder tool */}
      <div className="glass p-5 rounded-2xl relative overflow-hidden border border-zinc-850">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-1.5">
          <MapPin className="w-4 h-4 text-success" />
          Interactive Seat Finder
        </h3>

        <form onSubmit={handleLocateSeat} className="grid grid-cols-3 gap-2.5 mb-3">
          <div>
            <label className="text-[9px] text-zinc-500 font-semibold uppercase block mb-1">Section</label>
            <input
              type="text"
              required
              value={section}
              onChange={(e) => setSection(e.target.value)}
              placeholder="e.g. 114"
              className="w-full bg-zinc-900 border border-zinc-800 focus:border-success/50 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-600 outline-none transition-all duration-300"
            />
          </div>
          <div>
            <label className="text-[9px] text-zinc-500 font-semibold uppercase block mb-1">Row</label>
            <input
              type="text"
              value={row}
              onChange={(e) => setRow(e.target.value)}
              placeholder="F"
              className="w-full bg-zinc-900 border border-zinc-800 focus:border-success/50 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-600 outline-none transition-all duration-300"
            />
          </div>
          <div>
            <label className="text-[9px] text-zinc-500 font-semibold uppercase block mb-1">Seat</label>
            <input
              type="text"
              value={seat}
              onChange={(e) => setSeat(e.target.value)}
              placeholder="12"
              className="w-full bg-zinc-900 border border-zinc-800 focus:border-success/50 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-600 outline-none transition-all duration-300"
            />
          </div>
          <button
            type="submit"
            className="col-span-3 mt-1.5 w-full bg-zinc-900 hover:bg-success/15 hover:text-success border border-zinc-800 hover:border-success/30 text-white rounded-xl py-2 text-xs font-bold uppercase tracking-wider transition-all duration-300 cursor-pointer"
          >
            Locate Seating Coordinates
          </button>
        </form>

        {/* Seat finder result output */}
        {seatLocation && (
          <div className="mt-4 p-3.5 rounded-xl bg-success/5 border border-success/20 space-y-2 animate-fadeIn">
            <div className="flex justify-between items-center text-xs font-bold text-white">
              <span>Section {seatLocation.section} Located</span>
              <span className="text-[10px] text-success bg-success/10 border border-success/20 px-2 py-0.5 rounded uppercase font-extrabold tracking-wider">
                {seatLocation.gate} Entry
              </span>
            </div>
            <div className="text-[10px] text-zinc-400 font-light leading-relaxed">
              <strong>Route Directions:</strong> {seatLocation.directions}
            </div>
            <div className="flex gap-2 items-center text-[9px] text-zinc-500 font-semibold pt-1.5 border-t border-zinc-850">
              <span className="flex items-center gap-1 text-success">
                <Check className="w-3.5 h-3.5" /> Fast check-in open
              </span>
              <span>&bull;</span>
              <span>Zone: {seatLocation.zone}</span>
            </div>
          </div>
        )}
      </div>

      {/* Parking Guidance card */}
      <div className="glass p-5 rounded-2xl border border-zinc-850 relative">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-1.5">
          <Car className="w-4 h-4 text-success" />
          Smart Parking Guidance
        </h3>

        {bestParking && (
          <div className="mb-4 p-3.5 rounded-xl border border-success/20 bg-success/5 flex justify-between items-center gap-4">
            <div>
              <div className="text-xs font-bold text-white uppercase">Recommended Zone</div>
              <div className="text-[11px] font-bold text-success mt-0.5">{bestParking.name}</div>
              <p className="text-[9px] text-zinc-500 font-light mt-1">
                Currently has the shortest entrance delay and maximum spots open.
              </p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xl font-black text-white">{bestParking.available_spots}</div>
              <span className="text-[8px] text-zinc-500 font-semibold uppercase tracking-wider block">Spots Open</span>
            </div>
          </div>
        )}

        {/* Small parking summary rows */}
        <div className="grid grid-cols-2 gap-2">
          {parkingLots.map((lot) => (
            <div key={lot.name} className="p-3 rounded-xl bg-zinc-950/40 border border-zinc-900 flex justify-between items-center">
              <div>
                <span className="text-[10px] font-bold text-white block truncate max-w-[90px]">{lot.name}</span>
                <span className={`text-[8px] font-bold px-1 rounded uppercase tracking-wider inline-block mt-1 ${
                  lot.status === "FULL" ? "bg-danger/25 text-danger" : "bg-success/25 text-success"
                }`}>
                  {lot.status}
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-black text-zinc-200">{lot.available_spots}</span>
                <span className="text-[7px] text-zinc-500 font-semibold block uppercase">Available</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Live Transit Shuttle arrivals */}
      <div className="glass p-5 rounded-2xl border border-zinc-850">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-1.5">
          <Bus className="w-4 h-4 text-success" />
          Live Transit & Shuttles
        </h3>
        <div className="space-y-2.5">
          {transitVehicles.slice(0, 3).map((vehicle, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-zinc-950/40 border border-zinc-900 flex justify-between items-center">
              <div>
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  {vehicle.route}
                  <span className="text-[8px] bg-zinc-800 text-zinc-400 px-1 rounded uppercase font-bold tracking-wider">
                    {vehicle.type}
                  </span>
                </div>
                <div className="text-[9px] text-zinc-500 font-medium mt-1 leading-none">
                  Next stop: <strong className="text-zinc-400">{vehicle.current_stop || "Terminal"}</strong>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                  vehicle.status === "DELAYED" ? "bg-danger/10 border-danger/25 text-danger" : "bg-success/10 border-success/25 text-success"
                }`}>
                  {vehicle.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
