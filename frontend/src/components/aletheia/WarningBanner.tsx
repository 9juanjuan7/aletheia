import { AlertTriangle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface WarningBannerProps {
  warning: string;
  recommendation?: string;
  severity?: 'critical' | 'warning';
}

export function WarningBanner({ 
  warning, 
  recommendation,
  severity = 'warning'
}: WarningBannerProps) {
  const isCritical = severity === 'critical' || warning.includes('CRITICAL');

  return (
    <div className={cn(
      "border-l-2 pl-3 py-3",
      isCritical 
        ? "border-danger bg-danger-muted" 
        : "border-warning bg-warning-muted"
    )}>
      <div className="flex items-start gap-2">
        {isCritical ? (
          <AlertTriangle className="h-4 w-4 text-danger flex-shrink-0 mt-0.5" />
        ) : (
          <AlertCircle className="h-4 w-4 text-warning flex-shrink-0 mt-0.5" />
        )}
        <div className="space-y-1">
          <p className={cn(
            "text-sm font-semibold",
            isCritical ? "text-danger" : "text-warning-foreground"
          )}>
            {warning}
          </p>
          {recommendation && (
            <p className="text-sm text-foreground">
              {recommendation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
