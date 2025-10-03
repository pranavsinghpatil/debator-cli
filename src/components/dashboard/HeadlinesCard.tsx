import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Headline {
  title: string;
  sentiment: "positive" | "negative" | "neutral";
  confidence: number;
}

interface HeadlinesCardProps {
  headlines: Headline[];
}

export const HeadlinesCard = ({ headlines }: HeadlinesCardProps) => {
  const getSentimentVariant = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "default";
      case "negative":
        return "destructive";
      default:
        return "secondary";
    }
  };

  return (
    <TooltipProvider>
      <div className="space-y-3">
        {headlines.slice(0, 3).map((headline, index) => (
          <Tooltip key={index}>
            <TooltipTrigger asChild>
              <div className="flex items-start gap-2 cursor-pointer hover:bg-secondary/50 p-2 rounded-md transition-colors">
                <Badge variant={getSentimentVariant(headline.sentiment)} className="mt-0.5 shrink-0">
                  {headline.sentiment}
                </Badge>
                <p className="text-sm text-foreground line-clamp-2 flex-1">
                  {headline.title}
                </p>
              </div>
            </TooltipTrigger>
            <TooltipContent className="max-w-md">
              <p className="text-sm">{headline.title}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Confidence: {(headline.confidence * 100).toFixed(1)}%
              </p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
};
