interface SentimentCardProps {
  sentiment: "positive" | "negative" | "neutral";
  score: number;
}

export const SentimentCard = ({ sentiment, score }: SentimentCardProps) => {
  const getSentimentColor = () => {
    switch (sentiment) {
      case "positive":
        return "bg-success";
      case "negative":
        return "bg-destructive";
      default:
        return "bg-muted-foreground";
    }
  };

  const getSentimentText = () => {
    return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className={`h-4 w-4 rounded-full ${getSentimentColor()}`} />
        <span className="text-lg font-semibold text-foreground">
          {getSentimentText()}
        </span>
      </div>
      <div className="text-2xl font-bold text-foreground">
        Score: {score.toFixed(2)}
      </div>
      <div className="text-xs text-muted-foreground">
        Aggregated from latest news
      </div>
    </div>
  );
};
