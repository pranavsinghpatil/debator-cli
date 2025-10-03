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
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="time"
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "12px" }}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "12px" }}
          domain={['auto', 'auto']}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="price"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={false}
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
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
};
