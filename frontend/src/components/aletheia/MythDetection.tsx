import { AlertTriangle } from "lucide-react";

interface Myth {
  myth: string;
  reality: string;
}

interface MythDetectionProps {
  myths: Myth[];
}

export function MythDetection({ myths }: MythDetectionProps) {
  if (myths.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No known health myths detected.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {myths.map((myth, index) => (
        <div 
          key={index}
          className="border-l-2 border-warning bg-warning-muted pl-3 py-2"
        >
          <div className="flex items-start gap-2 mb-2">
            <AlertTriangle className="h-3.5 w-3.5 text-warning mt-0.5 flex-shrink-0" />
            <span className="text-sm font-semibold text-foreground">
              {myth.myth}
            </span>
          </div>
          <div className="pl-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Reality
            </p>
            <p className="text-sm text-foreground">
              {myth.reality}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
