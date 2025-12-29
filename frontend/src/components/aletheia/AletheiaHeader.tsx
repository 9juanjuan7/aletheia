import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AletheiaHeaderProps {
  onRefresh?: () => void;
  isLoading?: boolean;
}

export function AletheiaHeader({ onRefresh, isLoading }: AletheiaHeaderProps) {
  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-card">
      <div>
        <h1 className="text-lg font-bold tracking-tight text-foreground font-mono">
          ALETHEIA
        </h1>
        <p className="text-[10px] text-muted-foreground uppercase tracking-widest">
          Funding Conflict Analysis
        </p>
      </div>
      
      {onRefresh && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={isLoading}
          className="h-8 px-2 text-muted-foreground hover:text-foreground"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      )}
    </header>
  );
}
