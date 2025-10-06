import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface SentimentPieChartProps {
  data: Array<{
    sentiment: string;
    count: number;
  }>;
}

export const SentimentPieChart = ({ data }: SentimentPieChartProps) => {
  const COLORS = {
    Positive: "hsl(var(--success))",
    Negative: "hsl(var(--destructive))",
    Neutral: "hsl(var(--muted-foreground))",
  };

  const chartData = data.map((item) => ({
    name: item.sentiment,
    value: item.count,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          outerRadius={120}
          fill="hsl(var(--primary))"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={COLORS[entry.name as keyof typeof COLORS]} 
              opacity={0.9}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--popover))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "0.5rem",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          }}
          labelStyle={{ color: "hsl(var(--popover-foreground))", fontWeight: 600 }}
          itemStyle={{ color: "hsl(var(--popover-foreground))" }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          iconType="circle"
          wrapperStyle={{
            fontSize: "0.875rem",
            fontWeight: 500,
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};
