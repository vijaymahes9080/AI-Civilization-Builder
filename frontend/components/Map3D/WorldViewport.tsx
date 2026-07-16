import React, { useRef } from 'react';
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

function TerrainGrid({ width, height }: { width: number; height: number }) {
  // Generates flat grid terrain meshes
  const cells = [];
  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      // Mock terrain type based on a clean determinism
      const terrainType = ((x * 3 + y * 7) % 5); 
      cells.push(
        <mesh 
          key={`${x}-${y}`} 
          position={[x - width / 2, -0.5, y - height / 2]} 
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <planeGeometry args={[0.95, 0.95]} />
          <meshStandardMaterial color={TERRAIN_COLORS[terrainType] || '#4b5563'} roughness={0.8} />
        </mesh>
      );
    }
  }
  return <group>{cells}</group>;
}

function CitizenAgentMeshes({ width, height }: { width: number; height: number }) {
  const citizens = useSimulationStore((state) => Object.values(state.citizens));
  const selectedAgentId = useSimulationStore((state) => state.selectedAgentId);
  const selectAgent = useSimulationStore((state) => state.selectAgent);

  return (
    <group>
      {citizens.map((cit) => {
        const isSelected = selectedAgentId === cit.id;
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
              color={isSelected ? '#10b981' : '#f59e0b'} 
              emissive={isSelected ? '#10b981' : '#000000'}
              emissiveIntensity={isSelected ? 0.5 : 0}
            />
          </mesh>
        );
      })}
    </group>
  );
}

export default function WorldViewport() {
  const width = 50;
  const height = 50;

  return (
    <div className="w-full h-full bg-background rounded-lg border border-gray-800 overflow-hidden relative">
      <Canvas camera={{ position: [0, 25, 35], fov: 60 }}>
        <color attach="background" args={['#0d0f12']} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 20, 10]} intensity={0.8} castShadow />
        
        <TerrainGrid width={width} height={height} />
        <CitizenAgentMeshes width={width} height={height} />
        
        <OrbitControls maxPolarAngle={Math.PI / 2.1} minDistance={5} maxDistance={60} />
      </Canvas>
      <div className="absolute top-3 left-3 bg-panel px-3 py-1.5 rounded text-xs border border-gray-800 text-gray-400">
        Left-click + Drag to Orbit | Right-click to Pan | Scroll to Zoom
      </div>
    </div>
  );
}
