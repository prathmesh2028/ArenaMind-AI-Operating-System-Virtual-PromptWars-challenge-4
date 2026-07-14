"use client";

import React, { useState } from "react";
import { Coffee, Clock, ChefHat, ChevronRight } from "lucide-react";
import { getWaitLevelStyle } from "../../lib/utils";

interface FoodStall {
  id: string;
  name: string;
  category: string;
  location: string;
  menu: string[];
  queueDepth: number;
  /** Fans processed per minute. */
  processingRate: number;
}

export default function FoodView() {
  const [selectedStall, setSelectedStall] = useState<FoodStall | null>(null);

  const foodStalls: FoodStall[] = [
    {
      id: "f1",
      name: "Kickoff Burger & Grill",
      category: "Burgers & Fries",
      location: "Sector A Concourse",
      menu: ["Championship Beef Burger - $12.00", "Golden Gridiron Fries - $5.50", "Double Draft Beer - $10.00"],
      queueDepth: 45,
      processingRate: 5,
    },
    {
      id: "f2",
      name: "World Cup Tacos",
      category: "Mexican Street Food",
      location: "Sector C Concourse",
      menu: ["Striker Beef Tacos (3x) - $11.00", "Corner Nachos with Cheese - $7.00", "Lime Margarita - $9.00"],
      queueDepth: 18,
      processingRate: 6,
    },
    {
      id: "f3",
      name: "Green Field Organic Salads",
      category: "Healthy & Vegan",
      location: "Sector E Concourse",
      menu: ["Halftime Quinoa Salad - $10.50", "Vegan Power Wrap - $9.00", "Organic Green Juice - $6.50"],
      queueDepth: 5,
      processingRate: 4,
    },
    {
      id: "f4",
      name: "Pitchside Grill & Dogs",
      category: "Hot Dogs & Snacks",
      location: "Sector B Concourse",
      menu: ["Stretcher Footlong Hotdog - $8.50", "Goalpost Jumbo Pretzel - $6.00", "Soda Cup (Free Refills) - $4.50"],
      queueDepth: 62,
      processingRate: 8,
    },
  ];

  /** Calculate predicted queue wait time in minutes. */
  const getWaitTime = (stall: FoodStall): number => {
    return Math.ceil(stall.queueDepth / stall.processingRate);
  };

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-400">
          Stadium Concessions & Stalls
        </h2>
        <span className="text-[10px] text-zinc-500 font-light italic">
          Dynamic Queue Projections
        </span>
      </div>

      {selectedStall ? (
        // Detailed Menu view
        <div className="glass p-5 rounded-2xl border border-zinc-850 animate-fadeIn">
          <button
            onClick={() => setSelectedStall(null)}
            className="text-[10px] font-bold text-success hover:text-success-light uppercase tracking-wider mb-4 flex items-center gap-1 cursor-pointer"
          >
            &larr; Back to food list
          </button>

          <div className="flex justify-between items-start mb-4 pb-4 border-b border-zinc-900">
            <div>
              <h3 className="text-base font-extrabold text-white">{selectedStall.name}</h3>
              <p className="text-[10px] text-zinc-500 font-light mt-0.5">{selectedStall.location}</p>
            </div>
            <div className={`px-2.5 py-1 rounded-xl border text-xs font-bold shrink-0 ${getWaitLevelStyle(getWaitTime(selectedStall))}`}>
              {getWaitTime(selectedStall)} min wait
            </div>
          </div>

          <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2.5">Menu items</h4>
          <div className="space-y-2">
            {selectedStall.menu.map((item, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-zinc-950/40 border border-zinc-900 flex justify-between items-center text-xs">
                <span className="text-zinc-200 font-medium">{item.split(" - ")[0]}</span>
                <span className="font-bold text-white">{item.split(" - ")[1]}</span>
              </div>
            ))}
          </div>

          <button className="mt-5 w-full bg-success hover:bg-success-dark text-white rounded-xl py-2.5 text-xs font-bold uppercase tracking-wider transition-all duration-300 cursor-pointer flex items-center justify-center gap-1.5 shadow-lg shadow-success/15">
            <ChefHat className="w-4.5 h-4.5" />
            Place Mobile Order
          </button>
        </div>
      ) : (
        // Stalls list
        <div className="space-y-3">
          {foodStalls.map((stall) => {
            const waitTime = getWaitTime(stall);
            return (
              <div
                key={stall.id}
                onClick={() => setSelectedStall(stall)}
                className="p-4 rounded-2xl border border-zinc-900 bg-zinc-950/15 hover:border-zinc-800 hover:bg-zinc-900/10 cursor-pointer transition-all duration-300 flex justify-between items-center gap-4 group"
              >
                <div className="flex gap-3">
                  <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-850 flex items-center justify-center text-zinc-400 group-hover:scale-105 transition-transform duration-300 shrink-0">
                    <Coffee className="w-5 h-5 text-success" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white group-hover:text-success transition-colors duration-300">
                      {stall.name}
                    </h4>
                    <p className="text-[10px] text-zinc-500 font-light mt-0.5">{stall.location}</p>
                    <div className="flex items-center gap-1.5 mt-2 text-[9px] text-zinc-400 font-medium">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Est. Wait Time: {waitTime} mins</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className={`px-2 py-0.5 rounded border text-[9px] font-bold uppercase tracking-wider ${getWaitLevelStyle(waitTime)}`}>
                    {waitTime >= 10 ? "Busy" : waitTime >= 5 ? "Moderate" : "Short Wait"}
                  </div>
                  <ChevronRight className="w-4.5 h-4.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
