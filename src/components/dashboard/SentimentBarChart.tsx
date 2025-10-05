import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface SentimentDistribution {
  sentiment: string;
  count: number;
}

interface SentimentBarChartProps {
  data: SentimentDistribution[];
}

export const SentimentBarChart = ({ data }: SentimentBarChartProps) => {
  const colors = {
    Positive: "hsl(var(--success))",
    Negative: "hsl(var(--destructive))",
    Neutral: "hsl(var(--muted-foreground))",
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
        <XAxis
          dataKey="sentiment"
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "11px", fontWeight: 500 }}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "11px", fontWeight: 500 }}
          tickLine={false}
          axisLine={{ stroke: "hsl(var(--border))" }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "0.75rem",
            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
          }}
          cursor={{ fill: "hsl(var(--accent))", opacity: 0.1 }}
        />
        <Bar dataKey="count" radius={[12, 12, 0, 0]} maxBarSize={60}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={colors[entry.sentiment as keyof typeof colors]}
              opacity={0.9}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
