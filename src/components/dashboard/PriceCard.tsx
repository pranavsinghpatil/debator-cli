import { TrendingUp, TrendingDown } from "lucide-react";

interface PriceCardProps {
  ticker: string;
  price: number;
  change: number;
  changePercent: number;
}

export const PriceCard = ({ ticker, price, change, changePercent }: PriceCardProps) => {
  const isPositive = change >= 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-foreground">{ticker}</span>
        {isPositive ? (
          <TrendingUp className="h-5 w-5 text-success" />
        ) : (
          <TrendingDown className="h-5 w-5 text-destructive" />
        )}
      </div>
      <div className="space-y-1">
        <div className="text-3xl font-bold text-foreground">
          ₹{price.toFixed(2)}
        </div>
        <div
          className={`text-sm font-medium ${
            isPositive ? "text-success" : "text-destructive"
          }`}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(2)} ({isPositive ? "+" : ""}
          {changePercent.toFixed(2)}%)
        </div>
      </div>
    </div>
  );
};
