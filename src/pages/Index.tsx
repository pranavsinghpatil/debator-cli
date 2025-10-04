import { useState, useEffect } from "react";
import { InfoCard } from "@/components/dashboard/InfoCard";
import { PriceCard } from "@/components/dashboard/PriceCard";
import { SentimentCard } from "@/components/dashboard/SentimentCard";
import { HeadlinesCard } from "@/components/dashboard/HeadlinesCard";
import { StatusLogCard } from "@/components/dashboard/StatusLogCard";
import { PriceChart } from "@/components/dashboard/PriceChart";
import { SentimentBarChart } from "@/components/dashboard/SentimentBarChart";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Footer } from "@/components/Footer";

// Mock data types
interface LogEntry {
  timestamp: string;
  type: "success" | "error" | "info";
  message: string;
}

interface Headline {
  title: string;
  sentiment: "positive" | "negative" | "neutral";
  confidence: number;
}

interface PriceDataPoint {
  time: string;
  price: number;
  sentiment?: "positive" | "negative" | "neutral";
  headline?: string;
  confidence?: number;
}

const Index = () => {
  const [market, setMarket] = useState("indian");
  const [ticker, setTicker] = useState("RELIANCE");
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [logs, setLogs] = useState<LogEntry[]>([
    { timestamp: "10:30:01", type: "info", message: "Initializing dashboard..." },
    { timestamp: "10:30:02", type: "success", message: "Connected to market data feed" },
  ]);

  // Mock data
  const priceData = {
    ticker: ticker,
    price: 2450.75,
    change: 32.50,
    changePercent: 1.34,
  };

  const sentimentData = {
    sentiment: "positive" as const,
    score: 0.72,
  };

  const headlines: Headline[] = [
    {
      title: "Reliance Industries announces major expansion in renewable energy sector",
      sentiment: "positive",
      confidence: 0.89,
    },
    {
      title: "Market experts predict strong Q4 results for major conglomerates",
      sentiment: "positive",
      confidence: 0.76,
    },
    {
      title: "Concerns raised over global supply chain disruptions affecting exports",
      sentiment: "negative",
      confidence: 0.68,
    },
  ];

  const priceChartData: PriceDataPoint[] = [
    { time: "09:15", price: 2418.25 },
    { time: "09:30", price: 2422.50 },
    { time: "09:45", price: 2428.75, sentiment: "positive", headline: headlines[0].title, confidence: 0.89 },
    { time: "10:00", price: 2435.00 },
    { time: "10:15", price: 2440.25, sentiment: "positive", headline: headlines[1].title, confidence: 0.76 },
    { time: "10:30", price: 2438.50 },
    { time: "10:45", price: 2442.00, sentiment: "negative", headline: headlines[2].title, confidence: 0.68 },
    { time: "11:00", price: 2445.75 },
    { time: "11:15", price: 2450.75 },
  ];

  const sentimentDistribution = [
    { sentiment: "Positive", count: 15 },
    { sentiment: "Negative", count: 5 },
    { sentiment: "Neutral", count: 8 },
  ];

  const indianTickers = ["RELIANCE", "TCS", "INFY", "HDFC", "WIPRO"];
  const globalTickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"];

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString("en-US", { hour12: false });
      
      setLogs(prev => [
        ...prev,
        { timestamp: timeStr, type: "info" as const, message: `Fetching latest data for ${ticker}...` },
        { timestamp: timeStr, type: "success" as const, message: "Price data updated" },
        { timestamp: timeStr, type: "success" as const, message: "Sentiment analysis complete" },
      ].slice(-10)); // Keep last 10 logs
      
      setLastUpdate(now);
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [ticker]);

  const handleManualRefresh = () => {
    const now = new Date();
    const timeStr = now.toLocaleTimeString("en-US", { hour12: false });
    setLogs(prev => [
      ...prev,
      { timestamp: timeStr, type: "info" as const, message: "Manual refresh triggered" },
      { timestamp: timeStr, type: "success" as const, message: "Data refreshed successfully" },
    ].slice(-10));
    setLastUpdate(now);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="flex-1 p-4 md:p-6 max-w-[1600px] mx-auto w-full">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-1">
                📈 Rife-Trade
              </h1>
              <p className="text-muted-foreground text-sm">
                Real-time news, sentiment, and market prices
              </p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        {/* Market & Ticker Selection */}
        <div className="mb-6 bg-card border p-4 rounded-lg">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-muted-foreground">Market:</label>
              <Select value={market} onValueChange={setMarket}>
                <SelectTrigger className="w-[120px] h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="indian">Indian</SelectItem>
                  <SelectItem value="global">Global</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-muted-foreground">Ticker:</label>
              <Select value={ticker} onValueChange={setTicker}>
                <SelectTrigger className="w-[140px] h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(market === "indian" ? indianTickers : globalTickers).map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button onClick={handleManualRefresh} className="bg-primary hover:bg-primary/90" size="sm">
              <RefreshCw className="h-3 h-3 mr-1" />
              Refresh
            </Button>

            <div className="ml-auto text-xs text-muted-foreground bg-muted px-3 py-1 rounded">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Top Row - Info Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <InfoCard title="Ticker & Latest Price">
            <PriceCard {...priceData} />
          </InfoCard>

          <InfoCard title="Overall Sentiment">
            <SentimentCard {...sentimentData} />
          </InfoCard>

          <InfoCard title="Top Headlines">
            <HeadlinesCard headlines={headlines} />
          </InfoCard>

          <InfoCard title="Status / Logs">
            <StatusLogCard logs={logs} />
          </InfoCard>
        </div>

        {/* Middle Row - Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          <InfoCard title="Price & Sentiment Timeline" className="lg:col-span-3">
            <div className="h-[300px] w-full">
              <PriceChart data={priceChartData} />
            </div>
          </InfoCard>

          <InfoCard title="Sentiment Distribution" className="lg:col-span-2">
            <div className="h-[300px] w-full">
              <SentimentBarChart data={sentimentDistribution} />
            </div>
          </InfoCard>
        </div>

      </div>
      
      <Footer />
    </div>
  );
};

export default Index;
