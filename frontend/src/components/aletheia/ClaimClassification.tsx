import { AlertTriangle, CheckCircle, AlertCircle, Scale, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface ClaimClassificationProps {
  classification: string;
  warning?: string;
  redFlags?: string[];
}

export function ClaimClassification({
  classification,
  warning,
  redFlags = []
}: ClaimClassificationProps) {
  const getClassificationStyle = (classType: string) => {
    if (classType.includes('MANUFACTURED_CONSENSUS') || classType.includes('INDUSTRY_NARRATIVE')) {
      return {
        icon: AlertTriangle,
        color: 'text-danger',
        borderColor: 'border-danger',
        bgColor: 'bg-danger-muted'
      };
    }
    if (classType.includes('ESTABLISHED_FACT_VERIFIED')) {
      return {
        icon: CheckCircle,
        color: 'text-success',
        borderColor: 'border-success',
        bgColor: 'bg-success-muted'
      };
    }
    if (classType === 'FRINGE' || classType === 'COMMERCIAL_CLAIM') {
      return {
        icon: AlertCircle,
        color: 'text-warning',
        borderColor: 'border-warning',
        bgColor: 'bg-warning-muted'
      };
    }
    if (classType.includes('CONTESTED')) {
      return {
        icon: Scale,
        color: 'text-warning',
        borderColor: 'border-warning',
        bgColor: 'bg-warning-muted'
      };
    }
    return {
      icon: Info,
      color: 'text-muted-foreground',
      borderColor: 'border-border',
      bgColor: 'bg-muted'
    };
  };

  const classText = classification.replace(/_/g, ' ');
  const style = getClassificationStyle(classification);
  const Icon = style.icon;

  return (
    <div className={cn(
      "border-l-2 pl-3 py-3",
      style.borderColor,
      style.bgColor
    )}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={cn("h-4 w-4", style.color)} />
        <span className={cn(
          "text-sm font-semibold uppercase tracking-wide",
          style.color
        )}>
          {classText}
        </span>
      </div>

      {warning && (
        <p className="text-sm text-foreground mb-2 leading-relaxed">
          {warning}
        </p>
      )}

      {redFlags.length > 0 && (
        <ul className="space-y-1 mt-2">
          {redFlags.slice(0, 3).map((flag, index) => (
            <li key={index} className="text-xs text-muted-foreground flex items-start gap-2">
              <span className="text-muted-foreground">•</span>
              <span>{flag}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
