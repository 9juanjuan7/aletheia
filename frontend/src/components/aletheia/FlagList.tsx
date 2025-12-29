import { AlertTriangle, Check, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface FlagListProps {
  redFlags?: string[];
  greenFlags?: string[];
}

export function FlagList({ redFlags = [], greenFlags = [] }: FlagListProps) {
  if (redFlags.length === 0 && greenFlags.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No significant indicators detected.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {/* Red Flags */}
      {redFlags.length > 0 && (
        <div className="space-y-2">
          {redFlags.map((flag, index) => (
            <div 
              key={`red-${index}`}
              className="flex gap-2 text-sm"
            >
              <div className="flag-indicator flag-indicator-danger" />
              <div className="flex items-start gap-2 flex-1 py-1">
                <AlertTriangle className="h-3.5 w-3.5 text-danger mt-0.5 flex-shrink-0" />
                <span className="text-foreground">{flag}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Green Flags */}
      {greenFlags.length > 0 && (
        <div className="space-y-2">
          {greenFlags.map((flag, index) => (
            <div 
              key={`green-${index}`}
              className="flex gap-2 text-sm"
            >
              <div className="flag-indicator flag-indicator-success" />
              <div className="flex items-start gap-2 flex-1 py-1">
                <Check className="h-3.5 w-3.5 text-success mt-0.5 flex-shrink-0" />
                <span className="text-foreground">{flag}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
