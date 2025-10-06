import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon?: LucideIcon;
  suffix?: string;
}

export const MetricCard = ({ label, value, change, icon: Icon, suffix = "" }: MetricCardProps) => {
  const hasChange = change !== undefined;
  const isPositive = change && change >= 0;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {label}
        </span>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground/60" />}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-foreground">
          {value}{suffix}
        </span>
        {hasChange && (
          <span
            className={`text-xs font-semibold ${
              isPositive ? "text-success" : "text-destructive"
            }`}
          >
            {isPositive ? "+" : ""}
            {change?.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  );
};
