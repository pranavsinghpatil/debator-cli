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
      <div className="flex-1 p-4 md:p-6 lg:p-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-chart-5 bg-clip-text text-transparent mb-2">
                📈 Rife-Trade
              </h1>
              <p className="text-muted-foreground text-lg">
                Real-time news, sentiment, and market prices
              </p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        {/* Market & Ticker Selection */}
        <div className="mb-8 flex flex-wrap items-center gap-4 justify-between bg-gradient-to-r from-primary/5 to-chart-5/5 backdrop-blur-sm p-5 rounded-2xl border-2 border-primary/20">
          <div className="flex flex-wrap items-center gap-3">
            <Select value={market} onValueChange={setMarket}>
              <SelectTrigger className="w-[180px] bg-card border-primary/30">
                <SelectValue placeholder="Select Market" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="indian">Indian Market</SelectItem>
                <SelectItem value="global">Global Market</SelectItem>
              </SelectContent>
            </Select>

            <Select value={ticker} onValueChange={setTicker}>
              <SelectTrigger className="w-[180px] bg-card border-primary/30">
                <SelectValue placeholder="Select Ticker" />
              </SelectTrigger>
              <SelectContent>
                {(market === "indian" ? indianTickers : globalTickers).map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button onClick={handleManualRefresh} className="bg-primary hover:bg-primary/90" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <div className="text-sm font-medium text-foreground bg-card px-4 py-2 rounded-lg border border-primary/20">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>

        {/* Top Row - Info Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <InfoCard title="Ticker & Latest Price" className="bg-gradient-to-br from-primary/10 to-primary/5">
            <PriceCard {...priceData} />
          </InfoCard>

          <InfoCard title="Overall Sentiment" className="bg-gradient-to-br from-chart-2/10 to-chart-2/5">
            <SentimentCard {...sentimentData} />
          </InfoCard>

          <InfoCard title="Top Headlines" className="bg-gradient-to-br from-chart-4/10 to-chart-4/5">
            <HeadlinesCard headlines={headlines} />
          </InfoCard>

          <InfoCard title="Status / Logs" className="bg-gradient-to-br from-chart-5/10 to-chart-5/5">
            <StatusLogCard logs={logs} />
          </InfoCard>
        </div>

        {/* Middle Row - Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
          <InfoCard title="Price & Sentiment Timeline" className="lg:col-span-3 bg-gradient-to-br from-primary/5 to-chart-1/10">
            <div className="h-[350px] w-full">
              <PriceChart data={priceChartData} />
            </div>
          </InfoCard>

          <InfoCard title="Sentiment Distribution" className="lg:col-span-2 bg-gradient-to-br from-chart-2/5 to-chart-3/5">
            <div className="h-[350px] w-full">
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
