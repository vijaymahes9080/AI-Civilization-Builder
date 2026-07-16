import { create } from 'zustand';

export interface Citizen {
  id: string;
  name: string;
  age: number;
  health: number;
  wealth: number;
  pos_x: number;
  pos_y: number;
  occupation: string;
  inventory?: Record<string, number>;
  personality?: { o: number; c: number; e: number; a: number; n: number };
  is_sick?: boolean;
}

export interface SimEvent {
  event_id: string;
  tick: number;
  event_type: string;
  source_entity_id: string;
  description: string;
  metadata: any;
  timestamp: string;
}

interface SimulationState {
  worldId: string | null;
  tick: number;
  citizens: Record<string, Citizen>;
  events: SimEvent[];
  weather: string;
  selectedAgentId: string | null;
  isConnected: boolean;
  socket: WebSocket | null;
  width: number;
  height: number;
  terrainMap: number[][];
  burningCells: [number, number][];
  activeDisasters: any[];
  
  connectWorld: (worldId: string) => void;
  disconnect: () => void;
  selectAgent: (agentId: string | null) => void;
  sendSpeedCmd: (multiplier: number) => void;
  sendStepCmd: () => void;
  summonDisaster: (type: string, x: number, y: number) => void;
}

export const useSimulationStore = create<SimulationState>((set, get) => ({
  worldId: null,
  tick: 0,
  citizens: {},
  events: [],
  weather: "Sunny",
  selectedAgentId: null,
  isConnected: false,
  socket: null,
  width: 50,
  height: 50,
  terrainMap: [],
  burningCells: [],
  activeDisasters: [],

  connectWorld: (worldId: string) => {
    const existingSocket = get().socket;
    if (existingSocket) {
      existingSocket.close();
    }

    const wsUrl = `ws://localhost:8000/ws/simulation/${worldId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      set({ isConnected: true, socket: ws, worldId });
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "CONNECTION_ESTABLISHED") {
          set({
            worldId: msg.world_id,
            width: msg.width || 50,
            height: msg.height || 50,
            terrainMap: msg.terrain || [],
            citizens: msg.citizens || {}
          });
        } else if (msg.type === "SIM_EVENT") {
          const payload = msg.payload;
          
          set((state) => {
            const updatedEvents = [payload, ...state.events].slice(0, 100); // Limit to 100 events
            const updatedCitizens = { ...state.citizens };
            
            // Handle specific event updates to adjust citizen state on the fly
            if (payload.event_type === "SPAWNED") {
              const [x, y] = payload.metadata.coords;
              updatedCitizens[payload.source_entity_id] = {
                id: payload.source_entity_id,
                name: payload.description.split(" ")[0],
                age: 0,
                health: 100,
                wealth: 10,
                pos_x: x,
                pos_y: y,
                occupation: "Forager",
                is_sick: false
              };
            } else if (payload.event_type === "MOVED") {
              const agentId = payload.source_entity_id;
              const [x, y] = payload.metadata.new_pos;
              if (updatedCitizens[agentId]) {
                updatedCitizens[agentId].pos_x = x;
                updatedCitizens[agentId].pos_y = y;
              }
            } else if (payload.event_type === "DIED") {
              delete updatedCitizens[payload.source_entity_id];
            } else if (payload.event_type === "INFECTED") {
              const agentId = payload.source_entity_id;
              if (updatedCitizens[agentId]) {
                updatedCitizens[agentId].is_sick = true;
              }
            } else if (payload.event_type === "HEALED") {
              const agentId = payload.source_entity_id;
              if (updatedCitizens[agentId]) {
                updatedCitizens[agentId].is_sick = false;
              }
            } else if (payload.event_type === "TICK_HEARTBEAT") {
              const activeDisasters = payload.metadata.active_disasters || [];
              const burningCells = payload.metadata.burning_cells || [];
              return {
                tick: payload.tick,
                weather: payload.metadata.weather || state.weather,
                events: updatedEvents,
                activeDisasters,
                burningCells
              };
            }

            return {
              events: updatedEvents,
              citizens: updatedCitizens
            };
          });
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };

    ws.onclose = () => {
      set({ isConnected: false, socket: null });
    };
  },

  disconnect: () => {
    const ws = get().socket;
    if (ws) {
      ws.close();
    }
    set({ isConnected: false, socket: null, worldId: null });
  },

  selectAgent: (agentId: string | null) => {
    set({ selectedAgentId: agentId });
  },

  sendSpeedCmd: (multiplier: number) => {
    const ws = get().socket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "SET_SPEED", multiplier }));
    }
  },

  sendStepCmd: () => {
    const ws = get().socket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "STEP" }));
    }
  },

  summonDisaster: (type: string, x: number, y: number) => {
    const ws = get().socket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "SUMMON_DISASTER", disaster_type: type, x, y }));
    }
  }
}));
