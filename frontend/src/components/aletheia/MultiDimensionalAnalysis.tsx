import { cn } from "@/lib/utils";

interface ResearchSupportPattern {
  pattern: string;
  description: string;
}

interface MultiDimensionalAnalysisProps {
  funding_independence_score?: number;
  research_support_pattern?: ResearchSupportPattern;
  source_quality_score?: number;
  debate_status?: string;
  debate_description?: string;
  recommendation?: string;
  claims?: any[];
}

export function MultiDimensionalAnalysis({
  funding_independence_score = 0,
  research_support_pattern,
  source_quality_score = 0,
  debate_status = "UNKNOWN",
  debate_description = "",
  recommendation = "",
  claims = []
}: MultiDimensionalAnalysisProps) {
  
  const getScoreLevel = (score: number) => {
    if (score >= 7) return 'high';
    if (score >= 5) return 'medium';
    return 'low';
  };

  const getLevelStyles = (level: string) => {
    const levelStyles = {
      high: {
        barColor: 'bg-score-high',
        textColor: 'text-score-high',
        label: 'HIGH'
      },
      medium: {
        barColor: 'bg-score-medium',
        textColor: 'text-score-medium',
        label: 'MODERATE'
      },
      low: {
        barColor: 'bg-score-low',
        textColor: 'text-score-low',
        label: 'LOW'
      }
    };
    return levelStyles[level as keyof typeof levelStyles];
  };

  const ScoreSectionCard = ({ label, score }: { label: string; score: number }) => {
    const level = getScoreLevel(score);
    const styles = getLevelStyles(level);
    const percentage = (score / 10) * 100;
    
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

        {/* Label */}
        <div className="pt-1">
          <p className="text-sm font-semibold text-foreground">{label}</p>
        </div>
      </div>
    );
  };

  const getDebateStatusLabel = (status: string) => {
    switch (status) {
      case "LEGITIMATE_DEBATE":
        return 'Legitimate Debate';
      case "MANUFACTURED_CONSENSUS":
        return 'Manufactured Consensus';
      case "ESTABLISHED_FACT":
        return 'Established Fact';
      default:
        return 'Unknown';
    }
  };

  const getDebateStatusColor = (status: string) => {
    switch (status) {
      case "LEGITIMATE_DEBATE":
        return 'text-warning';
      case "MANUFACTURED_CONSENSUS":
        return 'text-danger';
      case "ESTABLISHED_FACT":
        return 'text-success';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <div className="space-y-4">
      {/* Three Dimensional Analysis */}
      <div className="space-y-4">
        <ScoreSectionCard label="Funding Independence" score={funding_independence_score} />
        
        {/* Research Support Pattern */}
        {research_support_pattern && (
          <div className="space-y-3">
            <div className="flex items-baseline gap-3">
              <span className="font-semibold text-foreground text-sm">
                {research_support_pattern.pattern}
              </span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {research_support_pattern.description}
            </p>
            <div className="pt-1">
              <p className="text-sm font-semibold text-foreground">Research Support</p>
            </div>
          </div>
        )}
        
        <ScoreSectionCard label="Source Quality" score={source_quality_score} />
      </div>

      {/* Debate Status */}
      {debate_status && (
        <div className="pt-2 border-t border-border space-y-1.5">
          <span className="data-label">Debate Status</span>
          <div className="flex items-baseline gap-2">
            <span className={cn(
              "font-mono text-sm font-semibold uppercase tracking-wide",
              getDebateStatusColor(debate_status)
            )}>
              {getDebateStatusLabel(debate_status)}
            </span>
          </div>
          {debate_description && (
            <p className="text-sm text-muted-foreground leading-relaxed">
              {debate_description}
            </p>
          )}
        </div>
      )}

      {/* Claims Analysis */}
      {claims && claims.length > 0 && (
        <div className="pt-2 border-t border-border space-y-2">
          <span className="data-label">Verified Claims</span>
          <div className="space-y-2.5">
            {claims.map((claim, idx) => (
              <div key={idx} className="text-sm space-y-1">
                <p className="text-foreground font-medium">{claim.claim}</p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  {claim.supporting_count !== undefined && (
                    <span>✓ {claim.supporting_count} supporting</span>
                  )}
                  {claim.contradicting_count !== undefined && (
                    <span>✗ {claim.contradicting_count} contradicting</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Nuanced Recommendation */}
      {recommendation && (
        <div className="pt-2 border-t border-border space-y-1.5">
          <span className="data-label">Recommendation</span>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {recommendation}
          </p>
        </div>
      )}
    </div>
  );
}
