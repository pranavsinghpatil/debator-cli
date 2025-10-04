import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

interface PriceTableData {
  date: string;
  price: number;
  change: number;
  changePercent: number;
}

interface PriceTableProps {
  data: PriceTableData[];
  ticker: string;
}

export const PriceTable = ({ data, ticker }: PriceTableProps) => {
  const downloadCSV = () => {
    const headers = ["Date", "Price", "Change", "Change %"];
    const csvContent = [
      headers.join(","),
      ...data.map(row => 
        `${row.date},${row.price},${row.change},${row.changePercent}`
      )
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${ticker}_price_history.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button onClick={downloadCSV} variant="outline" size="sm" className="h-7 px-3 text-xs">
          <Download className="w-3 h-3 mr-1" />
          Download CSV
        </Button>
      </div>
      <div className="rounded-lg border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Date</TableHead>
              <TableHead className="text-xs text-right">Price</TableHead>
              <TableHead className="text-xs text-right">Change</TableHead>
              <TableHead className="text-xs text-right">Change %</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, index) => (
              <TableRow key={index}>
                <TableCell className="text-xs font-medium">{row.date}</TableCell>
                <TableCell className="text-xs text-right">₹{row.price.toFixed(2)}</TableCell>
                <TableCell className={`text-xs text-right ${row.change >= 0 ? "text-success" : "text-destructive"}`}>
                  {row.change >= 0 ? "+" : ""}{row.change.toFixed(2)}
                </TableCell>
                <TableCell className={`text-xs text-right ${row.changePercent >= 0 ? "text-success" : "text-destructive"}`}>
                  {row.changePercent >= 0 ? "+" : ""}{row.changePercent.toFixed(2)}%
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
