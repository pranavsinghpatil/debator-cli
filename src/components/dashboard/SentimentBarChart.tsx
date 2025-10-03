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
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="sentiment"
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "12px" }}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          style={{ fontSize: "12px" }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "0.5rem",
          }}
        />
        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={colors[entry.sentiment as keyof typeof colors]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
