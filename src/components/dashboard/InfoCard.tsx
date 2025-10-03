import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ReactNode } from "react";

interface InfoCardProps {
  title: string;
  children: ReactNode;
  className?: string;
}

export const InfoCard = ({ title, children, className = "" }: InfoCardProps) => {
  return (
    <Card className={`shadow-sm border-border ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
};
