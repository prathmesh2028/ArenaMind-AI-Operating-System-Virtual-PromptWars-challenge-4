import React from "react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background px-4 py-16 relative overflow-hidden">
      {/* Background gradients for premium aesthetic */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[400px] h-[400px] bg-success/15 rounded-full blur-[100px] pointer-events-none" />

      {/* Header section */}
      <div className="z-10 text-center max-w-3xl mb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-semibold tracking-wider uppercase text-primary mb-6">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          FIFA World Cup 2026 Stadium OS
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-white mb-6">
          Arena<span className="text-primary">Mind</span> AI
        </h1>
        <p className="text-lg text-zinc-400 font-light max-w-xl mx-auto">
          The central intelligence operating system coordinating real-time stadium dynamics, crowd intelligence, transport, and emergencies.
        </p>
      </div>

      {/* Portal Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl w-full z-10">
        
        {/* Ops Command Center Card */}
        <div className="glass group hover:border-primary/50 transition-all duration-300 p-6 rounded-2xl flex flex-col justify-between cursor-pointer h-64">
          <div>
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Executive Command</h2>
            <p className="text-sm text-zinc-400 font-light">
              Real-time monitoring, stadium health gauges, incidents timeline, and Gemini predictive support.
            </p>
          </div>
          <span className="text-xs text-primary font-medium tracking-wide uppercase inline-flex items-center gap-1 group-hover:translate-x-1 transition-transform duration-300">
            Launch Portal &rarr;
          </span>
        </div>

        {/* Fan Portal Card */}
        <div className="glass group hover:border-success/50 transition-all duration-300 p-6 rounded-2xl flex flex-col justify-between cursor-pointer h-64">
          <div>
            <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center text-success mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Fan Experience</h2>
            <p className="text-sm text-zinc-400 font-light">
              Interactive stadium floorplans, food counter queues, waypoint routing, and translation tools.
            </p>
          </div>
          <span className="text-xs text-success font-medium tracking-wide uppercase inline-flex items-center gap-1 group-hover:translate-x-1 transition-transform duration-300">
            Launch Portal &rarr;
          </span>
        </div>

        {/* Volunteer Copilot Card */}
        <div className="glass group hover:border-warning/50 transition-all duration-300 p-6 rounded-2xl flex flex-col justify-between cursor-pointer h-64">
          <div>
            <div className="w-12 h-12 rounded-xl bg-warning/10 flex items-center justify-center text-warning mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Volunteer Copilot</h2>
            <p className="text-sm text-zinc-400 font-light">
              Active operational tasks boards, local speech-to-text ticket creation, and optimized routing.
            </p>
          </div>
          <span className="text-xs text-warning font-medium tracking-wide uppercase inline-flex items-center gap-1 group-hover:translate-x-1 transition-transform duration-300">
            Launch Portal &rarr;
          </span>
        </div>

        {/* Scenario Replay Card */}
        <div className="glass group hover:border-danger/50 transition-all duration-300 p-6 rounded-2xl flex flex-col justify-between cursor-pointer h-64">
          <div>
            <div className="w-12 h-12 rounded-xl bg-danger/10 flex items-center justify-center text-danger mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Scenario Replayer</h2>
            <p className="text-sm text-zinc-400 font-light">
              Interactive chronological replay console to track historic events, alerts, and resolution metrics.
            </p>
          </div>
          <span className="text-xs text-danger font-medium tracking-wide uppercase inline-flex items-center gap-1 group-hover:translate-x-1 transition-transform duration-300">
            Launch Portal &rarr;
          </span>
        </div>

      </div>

      {/* Footer copyright */}
      <div className="mt-20 text-xs text-zinc-600 font-light">
        ArenaMind AI &bull; World Cup 2026 Stadium Operating System &bull; Ready for deployment
      </div>
    </main>
  );
}
