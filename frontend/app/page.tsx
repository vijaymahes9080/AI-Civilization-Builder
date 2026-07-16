'use client';

import React, { useEffect, useState } from 'react';
import { useSimulationStore } from '../store/useSimulationStore';
import WorldViewport from '../components/Map3D/WorldViewport';
import EconomyChart from '../components/Charts/EconomyChart';
import { Play, Pause, FastForward, Activity, Globe, Compass, ShieldAlert, Cpu } from 'lucide-react';

export default function Dashboard() {
  const {
    worldId,
    tick,
    citizens,
    events,
    weather,
    selectedAgentId,
    isConnected,
    connectWorld,
    sendSpeedCmd,
    sendStepCmd,
    selectAgent
  } = useSimulationStore();

  const [activeSpeed, setActiveSpeed] = useState(1);
  const selectedCitizen = selectedAgentId ? citizens[selectedAgentId] : null;

  // Initialize connection on mount
  useEffect(() => {
    // Connect to demo world on mount
    connectWorld('demo-civilization-uuid');
  }, [connectWorld]);

  // Generate mock economy data based on tick progression for visualization stability
  const mockEconomyData = Array.from({ length: 20 }, (_, i) => {
    const tVal = Math.max(0, tick - 20 + i);
    return {
      tick: tVal,
      food: 1.0 + Math.sin(tVal * 0.1) * 0.2 + (tVal * 0.005),
      wood: 2.0 + Math.cos(tVal * 0.15) * 0.4 + (tVal * 0.002),
      stone: 3.0 + Math.sin(tVal * 0.05) * 0.1,
      iron: 5.0 + Math.cos(tVal * 0.2) * 0.8 + (tVal * 0.01)
    };
  });

  return (
    <main className="min-h-screen bg-background flex flex-col p-4 gap-4 text-gray-200">
      {/* Top Navbar */}
      <header className="flex items-center justify-between bg-panel border border-gray-800 px-6 py-4 rounded-lg">
        <div className="flex items-center gap-3">
          <Globe className="text-primary w-6 h-6 animate-pulse" />
          <div>
            <h1 className="text-lg font-bold tracking-wide">AI Civilization Builder</h1>
            <p className="text-xs text-gray-500">Persistent Multiverse Operating System</p>
          </div>
        </div>

        {/* Live Metrics */}
        <div className="flex gap-8 text-sm">
          <div className="flex flex-col items-center">
            <span className="text-gray-500 text-xs">SIMULATION TICK</span>
            <span className="font-mono text-primary font-bold text-lg">{tick}</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-gray-500 text-xs">POPULATION</span>
            <span className="font-mono text-accent font-bold text-lg">{Object.keys(citizens).length} Citizens</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="text-gray-500 text-xs">CLIMATE WEATHER</span>
            <span className="text-yellow-500 font-semibold text-lg">{weather}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-ping' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-400 font-mono">{isConnected ? 'WS_LIVE' : 'DISCONNECTED'}</span>
          </div>
        </div>

        {/* Timelines Controls */}
        <div className="flex gap-2">
          <button 
            onClick={() => { sendSpeedCmd(0); setActiveSpeed(0); }} 
            className={`p-2 rounded border border-gray-800 transition ${activeSpeed === 0 ? 'bg-primary text-white' : 'bg-panel hover:bg-gray-800'}`}
            title="Pause Simulation"
          >
            <Pause size={16} />
          </button>
          <button 
            onClick={() => { sendSpeedCmd(1); setActiveSpeed(1); }} 
            className={`p-2 rounded border border-gray-800 transition ${activeSpeed === 1 ? 'bg-primary text-white' : 'bg-panel hover:bg-gray-800'}`}
            title="Run 1x Speed"
          >
            <Play size={16} />
          </button>
          <button 
            onClick={() => { sendSpeedCmd(10); setActiveSpeed(10); }} 
            className={`p-2 rounded border border-gray-800 transition ${activeSpeed === 10 ? 'bg-primary text-white' : 'bg-panel hover:bg-gray-800'}`}
            title="Run 10x Speed"
          >
            <FastForward size={16} />
          </button>
          <button 
            onClick={sendStepCmd} 
            className="p-2 rounded border border-gray-800 bg-panel hover:bg-gray-800 text-gray-300 font-mono text-xs font-bold"
            title="Step One Tick"
          >
            STEP +1
          </button>
        </div>
      </header>

      {/* Main Content Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left Column: 3D Spatial Grid Viewport */}
        <div className="lg:col-span-2 flex flex-col h-[560px]">
          <WorldViewport />
        </div>

        {/* Right Column: Citizen Details & Charts */}
        <div className="flex flex-col gap-4">
          {/* Selected Citizen Card */}
          <div className="bg-panel border border-gray-800 p-5 rounded-lg flex-1 flex flex-col">
            <h3 className="text-sm font-bold text-gray-400 mb-3 flex items-center gap-1.5">
              <Cpu className="text-accent w-4 h-4" /> Agent Profiler
            </h3>
            
            {selectedCitizen ? (
              <div className="flex-1 flex flex-col gap-3 justify-between">
                <div>
                  <div className="flex justify-between items-start">
                    <span className="text-lg font-bold text-white">{selectedCitizen.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-accent font-semibold">{selectedCitizen.occupation}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-3 text-xs text-gray-400">
                    <div>Age: <span className="text-white font-mono">{selectedCitizen.age.toFixed(1)} cycles</span></div>
                    <div>Wealth: <span className="text-yellow-500 font-mono">${selectedCitizen.wealth.toFixed(1)}</span></div>
                    <div>Health: <span className="text-red-500 font-mono">{selectedCitizen.health.toFixed(0)}%</span></div>
                    <div>Coordinates: <span className="text-blue-500 font-mono">[{selectedCitizen.pos_x}, {selectedCitizen.pos_y}]</span></div>
                  </div>
                </div>

                <div className="border-t border-gray-800 pt-3">
                  <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Decisions & Logic</span>
                  <p className="text-xs italic text-gray-300">"Decided to explore local forests to secure wood stock. Expected action complete in 4 ticks."</p>
                </div>

                <button 
                  onClick={() => selectAgent(null)} 
                  className="w-full py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 border border-gray-700 transition mt-2"
                >
                  Clear Selection
                </button>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500">
                <Compass className="w-10 h-10 text-gray-700 mb-2" />
                <p className="text-xs">No citizen selected.</p>
                <p className="text-[10px] text-gray-600 mt-1 max-w-[200px]">Click any agent sphere on the 3D viewport to inspect personality, inventory and plans.</p>
              </div>
            )}
          </div>

          {/* D3 Economy Chart */}
          <EconomyChart data={mockEconomyData} />
        </div>
      </div>

      {/* Bottom Log Feed */}
      <footer className="bg-panel border border-gray-800 rounded-lg p-4 max-h-[200px] flex flex-col overflow-hidden">
        <h3 className="text-xs font-bold text-gray-400 mb-2 uppercase tracking-widest flex items-center gap-1">
          <Activity className="text-primary w-4 h-4" /> Live Event History Feed (DuckDB Log Stream)
        </h3>
        <div className="flex-1 overflow-y-auto font-mono text-[11px] text-gray-400 space-y-1.5 pr-2">
          {events.length === 0 ? (
            <div className="text-gray-600 text-center py-4">Waiting for simulation events...</div>
          ) : (
            events.map((ev) => (
              <div key={ev.event_id} className="flex gap-4 border-b border-gray-900 pb-1">
                <span className="text-primary font-semibold">T-{ev.tick}</span>
                <span className="text-accent font-bold">[{ev.event_type}]</span>
                <span className="flex-1 text-gray-300">{ev.description}</span>
                <span className="text-gray-600 text-[10px]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
              </div>
            ))
          )}
        </div>
      </footer>
    </main>
  );
}
