import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface TrendChartProps {
  type?: 'line' | 'bar'
  data: Record<string, unknown>[]
  dataKeys: { key: string; color: string; label: string }[]
  xKey?: string
  height?: number
  title?: string
}

export default function TrendChart({ type = 'line', data, dataKeys, xKey = 'name', height = 220, title }: TrendChartProps) {
  return (
    <div className="glass rounded-2xl p-5">
      {title && <h3 className="text-sm font-semibold text-white mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        {type === 'line' ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey={xKey} tick={{ fill: '#666680', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#666680', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: 'rgba(10,10,26,0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '12px',
              }}
            />
            {dataKeys.map((dk) => (
              <Line key={dk.key} type="monotone" dataKey={dk.key} stroke={dk.color} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey={xKey} tick={{ fill: '#666680', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#666680', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: 'rgba(10,10,26,0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '12px',
              }}
            />
            {dataKeys.map((dk) => (
              <Bar key={dk.key} dataKey={dk.key} fill={dk.color} radius={[6, 6, 0, 0]} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
