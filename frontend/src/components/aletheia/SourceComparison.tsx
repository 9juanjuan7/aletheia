import { ExternalLink, ArrowRightLeft } from "lucide-react";
import { CredibilityScore } from "./CredibilityScore";
import { cn } from "@/lib/utils";

interface SourceData {
  name: string;
  domain?: string;
  score: number;
  url?: string;
  title?: string;
  fundingSources?: string[];
}

interface SourceComparisonProps {
  mainSource: SourceData;
  evidenceSource?: SourceData;
  label?: string;
  fundingDiversity?: number;
}

export function SourceComparison({
  mainSource,
  evidenceSource,
  label = "Alternative Evidence",
  fundingDiversity
}: SourceComparisonProps) {
  const scoreDifference = evidenceSource 
    ? Math.abs(mainSource.score - evidenceSource.score)
    : 0;

  const showWarning = scoreDifference >= 3;

  const getDiversityLevel = (diversity?: number) => {
    if (!diversity) return null;
    if (diversity >= 60) return { label: 'High', color: 'text-success' };
    if (diversity >= 30) return { label: 'Moderate', color: 'text-warning' };
    return { label: 'Low', color: 'text-danger' };
  };

  const diversityLevel = getDiversityLevel(fundingDiversity);

  return (
    <div className="space-y-4">
      {/* Comparison Header */}
      {showWarning && (
        <div className="border-l-2 border-warning bg-warning-muted pl-3 py-2 mb-4">
          <p className="text-xs font-semibold text-warning uppercase tracking-wider mb-1">
            Credibility Gap Detected
          </p>
          <p className="text-sm text-foreground">
            {scoreDifference.toFixed(1)} point difference between sources. 
            Review both perspectives carefully.
          </p>
        </div>
      )}

      {/* Source Cards */}
      <div className="grid grid-cols-1 gap-3">
        {/* Main Source */}
        <div className="border border-border p-3">
          <p className="data-label mb-2">Main Source</p>
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">
              {mainSource.name}
            </span>
            <CredibilityScore score={mainSource.score} compact />
          </div>
        </div>

        {/* Evidence Source */}
        {evidenceSource && (
          <>
            <div className="flex items-center justify-center">
              <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
            </div>
            
            <div className="border border-border p-3">
              <p className="data-label mb-2">{label}</p>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-foreground">
                  {evidenceSource.name}
                </span>
                <CredibilityScore score={evidenceSource.score} compact />
              </div>
              
              {evidenceSource.title && evidenceSource.url && (
                <a 
                  href={evidenceSource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-primary hover:underline mt-2"
                >
                  <span className="line-clamp-1">{evidenceSource.title}</span>
                  <ExternalLink className="h-3 w-3 flex-shrink-0" />
                </a>
              )}

              {evidenceSource.fundingSources && evidenceSource.fundingSources.length > 0 && (
                <p className="text-xs text-muted-foreground mt-2">
                  <span className="font-medium">Funding:</span>{' '}
                  {evidenceSource.fundingSources.slice(0, 2).join(', ')}
                </p>
              )}
            </div>
          </>
        )}
      </div>

      {/* Funding Diversity */}
      {diversityLevel && (
        <div className="flex items-center justify-between text-xs border-t border-border pt-3">
          <span className="text-muted-foreground font-medium">Funding Diversity</span>
          <div className="flex items-center gap-2">
            <span className={cn("font-mono font-semibold", diversityLevel.color)}>
              {fundingDiversity?.toFixed(0)}%
            </span>
            <span className={cn("text-xs", diversityLevel.color)}>
              {diversityLevel.label}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
