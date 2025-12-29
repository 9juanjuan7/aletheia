import { cn } from "@/lib/utils";

interface CredibilityScoreProps {
  score: number;
  name?: string;
  explanation?: string;
  compact?: boolean;
}

export function CredibilityScore({ 
  score, 
  name, 
  explanation,
  compact = false 
}: CredibilityScoreProps) {
  const getScoreLevel = (score: number) => {
    if (score >= 7) return 'high';
    if (score >= 5) return 'medium';
    return 'low';
  };

  const level = getScoreLevel(score);
  const percentage = (score / 10) * 100;

  const levelStyles = {
    high: {
      barColor: 'bg-score-high',
      textColor: 'text-score-high',
      label: 'HIGH CREDIBILITY'
    },
    medium: {
      barColor: 'bg-score-medium',
      textColor: 'text-score-medium',
      label: 'MODERATE CREDIBILITY'
    },
    low: {
      barColor: 'bg-score-low',
      textColor: 'text-score-low',
      label: 'LOW CREDIBILITY'
    }
  };

  const styles = levelStyles[level];

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className={cn("font-mono text-sm font-semibold", styles.textColor)}>
          {score.toFixed(1)}
        </span>
        <div className="score-bar flex-1 max-w-16">
          <div 
            className={cn("score-bar-fill", styles.barColor)}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Score Display */}
      <div className="flex items-baseline gap-3">
        <span className={cn(
          "font-mono text-3xl font-bold tracking-tight",
          styles.textColor
        )}>
          {score.toFixed(1)}
        </span>
        <span className="font-mono text-sm text-muted-foreground">/10</span>
        <span className={cn(
          "ml-auto text-xs font-semibold uppercase tracking-wider",
          styles.textColor
        )}>
          {styles.label}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="score-bar">
        <div 
          className={cn("score-bar-fill", styles.barColor)}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Source Name & Explanation */}
      {(name || explanation) && (
        <div className="pt-2 border-t border-border">
          {name && (
            <p className="text-sm font-semibold text-foreground">{name}</p>
          )}
          {explanation && (
            <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
              {explanation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
