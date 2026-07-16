import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface DataPoint {
  tick: number;
  food: number;
  wood: number;
  stone: number;
  iron: number;
}

interface EconomyChartProps {
  data: DataPoint[];
}

export default function EconomyChart({ data }: EconomyChartProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 30, bottom: 30, left: 40 };
    const width = 450 - margin.left - margin.right;
    const height = 220 - margin.top - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // X scale
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.tick) as [number, number])
      .range([0, width]);

    // Y scale
    const maxVal = d3.max(data, d => Math.max(d.food, d.wood, d.stone, d.iron)) || 10;
    const y = d3.scaleLinear()
      .domain([0, maxVal * 1.1])
      .range([height, 0]);

    // X Axis
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(5))
      .attr('color', '#4b5563');

    // Y Axis
    g.append('g')
      .call(d3.axisLeft(y).ticks(5))
      .attr('color', '#4b5563');

    // Gridlines
    g.append('g')
      .attr('class', 'grid')
      .attr('opacity', 0.1)
      .call(d3.axisLeft(y).tickSize(-width).tickFormat(null));

    // Lines definitions
    const addLine = (key: keyof Omit<DataPoint, 'tick'>, color: string) => {
      const line = d3.line<DataPoint>()
        .x(d => x(d.tick))
        .y(d => y(d[key] as number))
        .curve(d3.curveMonotoneX);

      g.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('d', line);
    };

    addLine('food', '#ef4444');  // Red
    addLine('wood', '#10b981');  // Green
    addLine('stone', '#6b7280'); // Gray
    addLine('iron', '#3b82f6');  // Blue

  }, [data]);

  return (
    <div className="bg-panel border border-gray-800 p-4 rounded-lg">
      <h3 className="text-sm font-semibold text-gray-300 mb-2">Market Price Discoveries</h3>
      <svg ref={svgRef} width="450" height="220" className="mx-auto" />
      <div className="flex gap-4 justify-center mt-2 text-xs text-gray-400">
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded"></span>Food</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-emerald-500 rounded"></span>Wood</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-gray-500 rounded"></span>Stone</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded"></span>Iron</span>
      </div>
    </div>
  );
}
