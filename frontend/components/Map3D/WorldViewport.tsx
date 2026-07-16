import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { useSimulationStore } from '../../store/useSimulationStore';

const TERRAIN_COLORS: Record<number, string> = {
  0: '#1e3a8a', // Water: Deep Blue
  1: '#4d7c0f', // Plain: Lime Green
  2: '#065f46', // Forest: Emerald Green
  3: '#374151', // Mountain: Dark Slate Gray
  4: '#b45309', // Desert: Warm Brown
};

interface GridProps {
  width: number;
  height: number;
  onCellClick: (x: number, y: number) => void;
}

function TerrainGrid({ width, height, onCellClick }: GridProps) {
  const terrainMap = useSimulationStore((state) => state.terrainMap);
  const cells = [];

  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      // Read terrain from the synced array or calculate placeholder
      const terrainType = terrainMap && terrainMap[x] ? terrainMap[x][y] : ((x * 3 + y * 7) % 5);
      cells.push(
        <mesh 
          key={`${x}-${y}`} 
          position={[x - width / 2, -0.5, y - height / 2]} 
          rotation={[-Math.PI / 2, 0, 0]}
          onClick={(e) => {
            e.stopPropagation();
            onCellClick(x, y);
          }}
        >
          <planeGeometry args={[0.95, 0.95]} />
          <meshStandardMaterial color={TERRAIN_COLORS[terrainType] || '#4b5563'} roughness={0.8} />
        </mesh>
      );
    }
  }
  return <group>{cells}</group>;
}

function BurningFires({ width, height }: { width: number; height: number }) {
  const burningCells = useSimulationStore((state) => state.burningCells);

  return (
    <group>
      {burningCells.map(([x, y], idx) => (
        <group key={`${x}-${y}-${idx}`} position={[x - width / 2, 0.1, y - height / 2]}>
          {/* Main Fire Core */}
          <mesh>
            <boxGeometry args={[0.7, 0.7, 0.7]} />
            <meshStandardMaterial 
              color="#ea580c" 
              emissive="#f97316" 
              emissiveIntensity={2.0} 
              roughness={0.2} 
            />
          </mesh>
          {/* Internal Ember */}
          <mesh position={[0, 0.4, 0]}>
            <sphereGeometry args={[0.3, 8, 8]} />
            <meshBasicMaterial color="#ef4444" />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function MeteorStrikeVisuals({ width, height }: { width: number; height: number }) {
  const activeDisasters = useSimulationStore((state) => state.activeDisasters);
  const meteors = activeDisasters.filter((d: any) => d.type === 'METEOR');

  return (
    <group>
      {meteors.map((m: any, i: number) => {
        // Falling height animation based on ticks remaining (3 down to 1)
        const h = Math.max(0.5, m.ticks_remaining * 3.5);
        return (
          <group key={i} position={[m.x - width / 2, h, m.y - height / 2]}>
            {/* Meteor Rock Core */}
            <mesh>
              <sphereGeometry args={[1.0, 16, 16]} />
              <meshStandardMaterial color="#b91c1c" emissive="#ef4444" emissiveIntensity={3.5} />
            </mesh>
            {/* Fire Tail */}
            <mesh position={[0, 1.2, 0]}>
              <coneGeometry args={[0.7, 2.0, 8]} />
              <meshStandardMaterial color="#f97316" emissive="#ea580c" emissiveIntensity={2} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

function CitizenAgentMeshes({ width, height }: { width: number; height: number }) {
  const citizens = useSimulationStore((state) => Object.values(state.citizens));
  const selectedAgentId = useSimulationStore((state) => state.selectedAgentId);
  const selectAgent = useSimulationStore((state) => state.selectAgent);

  return (
    <group>
      {citizens.map((cit) => {
        const isSelected = selectedAgentId === cit.id;
        const isSick = !!cit.is_sick;
        // Selection is Blue, Sick is Green, normal is Gold
        const color = isSelected ? '#3b82f6' : (isSick ? '#10b981' : '#f59e0b');
        const glowColor = isSelected ? '#3b82f6' : (isSick ? '#10b981' : '#000000');
        
        return (
          <mesh
            key={cit.id}
            position={[cit.pos_x - width / 2, 0, cit.pos_y - height / 2]}
            onClick={(e) => {
              e.stopPropagation();
              selectAgent(cit.id);
            }}
          >
            <sphereGeometry args={[0.4, 16, 16]} />
            <meshStandardMaterial 
              color={color} 
              emissive={glowColor}
              emissiveIntensity={isSelected || isSick ? 0.8 : 0}
            />
          </mesh>
        );
      })}
    </group>
  );
}

interface WorldViewportProps {
  onCellClick: (x: number, y: number) => void;
}

export default function WorldViewport({ onCellClick }: WorldViewportProps) {
  const width = useSimulationStore((state) => state.width) || 50;
  const height = useSimulationStore((state) => state.height) || 50;

  return (
    <div className="w-full h-full bg-background rounded-lg border border-gray-800 overflow-hidden relative">
      <Canvas camera={{ position: [0, 25, 35], fov: 60 }}>
        <color attach="background" args={['#0d0f12']} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 20, 10]} intensity={0.8} castShadow />
        
        <TerrainGrid width={width} height={height} onCellClick={onCellClick} />
        <BurningFires width={width} height={height} />
        <MeteorStrikeVisuals width={width} height={height} />
        <CitizenAgentMeshes width={width} height={height} />
        
        <OrbitControls maxPolarAngle={Math.PI / 2.1} minDistance={5} maxDistance={60} />
      </Canvas>
      <div className="absolute top-3 left-3 bg-panel px-3 py-1.5 rounded text-xs border border-gray-800 text-gray-400">
        Left-click + Drag to Orbit | Right-click to Pan | Scroll to Zoom | Click terrain to target a disaster
      </div>
    </div>
  );
}
