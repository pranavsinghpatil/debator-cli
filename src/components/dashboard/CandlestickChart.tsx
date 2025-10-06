import { ResponsiveContainer, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Bar, Cell } from "recharts";

interface CandleDataPoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface CandlestickChartProps {
  data: CandleDataPoint[];
}

export const CandlestickChart = ({ data }: CandlestickChartProps) => {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const isPositive = data.close >= data.open;
      return (
        <div className="bg-card border border-border p-3 rounded-md shadow-lg">
          <p className="text-sm font-semibold text-foreground mb-2">
            {data.time}
          </p>
          <div className="space-y-1 text-xs">
            <p className="text-muted-foreground">Open: <span className="text-foreground font-medium">₹{data.open}</span></p>
            <p className="text-muted-foreground">High: <span className="text-success font-medium">₹{data.high}</span></p>
            <p className="text-muted-foreground">Low: <span className="text-destructive font-medium">₹{data.low}</span></p>
            <p className="text-muted-foreground">Close: <span className={`font-medium ${isPositive ? 'text-success' : 'text-destructive'}`}>₹{data.close}</span></p>
          </div>
        </div>
      );
    }
    return null;
  };

  const candleData = data.map((d) => ({
    ...d,
    isPositive: d.close >= d.open,
    body: [Math.min(d.open, d.close), Math.max(d.open, d.close)],
    wick: [d.low, d.high],
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={candleData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <defs>
          <linearGradient id="candleGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.1}/>
            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
        <XAxis
          dataKey="time"
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "11px", fontWeight: 500 }}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
        />
        <YAxis
          domain={['dataMin - 10', 'dataMax + 10']}
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "11px", fontWeight: 500 }}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
          tickFormatter={(value) => `₹${value}`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--border))", strokeWidth: 1 }} />
        <Bar dataKey="body" fill="hsl(var(--primary))" maxBarSize={20}>
          {candleData.map((entry, index) => (
            <Cell
              key={`body-${index}`}
              fill={entry.isPositive ? "hsl(var(--success))" : "hsl(var(--destructive))"}
              opacity={0.9}
            />
          ))}
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  );
};
