import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Scatter,
  ComposedChart,
} from "recharts";

interface PriceDataPoint {
  time: string;
  price: number;
  sentiment?: "positive" | "negative" | "neutral";
  headline?: string;
  confidence?: number;
}

interface PriceChartProps {
  data: PriceDataPoint[];
}

export const PriceChart = ({ data }: PriceChartProps) => {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border p-3 rounded-md shadow-lg">
          <p className="text-sm font-semibold text-foreground">
            Time: {data.time}
          </p>
          <p className="text-sm text-foreground">Price: ₹{data.price}</p>
          {data.headline && (
            <>
              <p className="text-xs text-muted-foreground mt-2 max-w-xs">
                {data.headline}
              </p>
              <p className="text-xs text-primary mt-1">
                Sentiment: {data.sentiment} ({(data.confidence * 100).toFixed(1)}%)
              </p>
            </>
          )}
        </div>
      );
    }
    return null;
  };

  const sentimentData = data.filter((d) => d.sentiment);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <defs>
          <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
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
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "11px", fontWeight: 500 }}
          domain={['auto', 'auto']}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
          tickFormatter={(value) => `₹${value}`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--border))", strokeWidth: 1 }} />
        <Line
          type="monotone"
          dataKey="price"
          stroke="hsl(var(--primary))"
          strokeWidth={3}
          dot={false}
          activeDot={{ r: 6, strokeWidth: 2, stroke: "hsl(var(--card))" }}
        />
        {sentimentData.map((entry, index) => (
          <Scatter
            key={index}
            data={[entry]}
            dataKey="price"
            fill={
              entry.sentiment === "positive"
                ? "hsl(var(--success))"
                : entry.sentiment === "negative"
                ? "hsl(var(--destructive))"
                : "hsl(var(--muted-foreground))"
            }
            shape="circle"
            r={6}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
};
