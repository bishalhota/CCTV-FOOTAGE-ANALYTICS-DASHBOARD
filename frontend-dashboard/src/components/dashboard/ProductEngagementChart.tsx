import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

/**
 * Mock data for Purplle Store Product Display Section engagement.
 */
const productEngagementData = [
  { name: 'Lipsticks', interactions: 345, color: '#ec4899' }, // Pink
  { name: 'Foundations', interactions: 280, color: '#f59e0b' }, // Amber
  { name: 'Perfumes', interactions: 190, color: '#8b5cf6' }, // Purple
  { name: 'Skincare', interactions: 410, color: '#10b981' }, // Green
  { name: 'Eyeshadows', interactions: 150, color: '#06b6d4' }, // Cyan
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-recharts-tooltip frosted-glass">
        <p className="tooltip-label">{label}</p>
        <p style={{ color: data.color, fontWeight: 700, fontSize: '0.9rem' }}>
          {data.interactions} Interactions
        </p>
      </div>
    );
  }
  return null;
};

export const ProductEngagementChart: React.FC = () => {
  return (
    <div className="chart-card frosted-glass">
      <h3>
        Product Display Engagement
        <span className="text-muted" style={{ fontSize: '0.75rem', fontWeight: 400 }}>
          Top Categories
        </span>
      </h3>
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <BarChart 
            data={productEngagementData} 
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            barSize={40}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="name" 
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
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
            <Bar 
              dataKey="interactions" 
              radius={[6, 6, 0, 0]}
              animationDuration={2000}
            >
              {productEngagementData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
