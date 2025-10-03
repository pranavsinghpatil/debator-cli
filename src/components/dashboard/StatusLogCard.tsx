import { useEffect, useRef } from "react";
import { CheckCircle2, XCircle, Info } from "lucide-react";

interface LogEntry {
  timestamp: string;
  type: "success" | "error" | "info";
  message: string;
}

interface StatusLogCardProps {
  logs: LogEntry[];
}

export const StatusLogCard = ({ logs }: StatusLogCardProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="h-3 w-3 text-terminal-success shrink-0" />;
      case "error":
        return <XCircle className="h-3 w-3 text-terminal-error shrink-0" />;
      default:
        return <Info className="h-3 w-3 text-primary shrink-0" />;
    }
  };

  const getTextColor = (type: string) => {
    switch (type) {
      case "success":
        return "text-terminal-success";
      case "error":
        return "text-terminal-error";
      default:
        return "text-terminal-text";
    }
  };

  return (
    <div
      ref={scrollRef}
      className="h-full max-h-[200px] overflow-y-auto bg-terminal-bg rounded-md p-3 font-mono text-xs space-y-2"
    >
      {logs.map((log, index) => (
        <div key={index} className="flex items-start gap-2">
          {getIcon(log.type)}
          <div className="flex-1 min-w-0">
            <span className="text-muted-foreground">[{log.timestamp}]</span>{" "}
            <span className={getTextColor(log.type)}>{log.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
