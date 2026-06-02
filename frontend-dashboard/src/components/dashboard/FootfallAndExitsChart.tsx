import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

/**
 * Mock data generation for Footfall (Entries) and Exits over time.
 * We'll simulate 12 hours of store operation.
 */
const generateFootfallData = () => {
  const data = [];
  let currentPeople = 0;
  const startHour = 9; // 9 AM

  for (let i = 0; i <= 12; i++) {
    const hour = startHour + i;
    const timeLabel = `${hour > 12 ? hour - 12 : hour}:00 ${hour >= 12 ? 'PM' : 'AM'}`;
    
    // Simulate natural store traffic bell curve
    const trafficMultiplier = Math.sin((i / 12) * Math.PI); 
    const entries = Math.floor(trafficMultiplier * 120) + Math.floor(Math.random() * 20);
    const exits = i === 0 ? 0 : Math.floor(trafficMultiplier * 110) + Math.floor(Math.random() * 25);
    
    currentPeople += (entries - exits);
    if (currentPeople < 0) currentPeople = 0;

    data.push({
      time: timeLabel,
      Entries: entries,
      Exits: exits,
      InStore: currentPeople
    });
  }
  return data;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-recharts-tooltip frosted-glass">
        <p className="tooltip-label">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color, fontWeight: 600, fontSize: '0.85rem' }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const FootfallAndExitsChart: React.FC = () => {
  const data = useMemo(() => generateFootfallData(), []);

  return (
    <div className="chart-card frosted-glass">
      <h3>
        Store Traffic Flow
        <span className="text-muted" style={{ fontSize: '0.75rem', fontWeight: 400 }}>
          Today (Entries vs Exits)
        </span>
      </h3>
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorEntries" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorExits" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="time" 
              stroke="#64748b" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="Entries" 
              stroke="#10b981" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorEntries)" 
              animationDuration={2000}
            />
            <Area 
              type="monotone" 
              dataKey="Exits" 
              stroke="#ef4444" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorExits)" 
              animationDuration={2000}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
