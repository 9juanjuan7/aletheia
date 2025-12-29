import { Building2, Coins, Eye, Link2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface FundingInfoProps {
  ownership?: string;
  fundingSources?: string[];
  conflictsOfInterest?: string[];
  industryTies?: string[];
  fundingTransparency?: string;
  isAcademic?: boolean;
  isGovernment?: boolean;
}

export function FundingInfo({
  ownership,
  fundingSources = [],
  conflictsOfInterest = [],
  industryTies = [],
  fundingTransparency,
  isAcademic = false,
  isGovernment = false
}: FundingInfoProps) {
  const getTransparencyColor = (level?: string) => {
    switch (level) {
      case 'high': return 'text-success';
      case 'medium': return 'text-warning';
      case 'low': 
      case 'none': return 'text-danger';
      default: return 'text-muted-foreground';
    }
  };

  const getTransparencyLabel = (level?: string) => {
    switch (level) {
      case 'high': return 'HIGH';
      case 'medium': return 'MODERATE';
      case 'low': return 'LOW';
      case 'none': return 'NONE';
      default: return 'UNKNOWN';
    }
  };

  return (
    <div className="space-y-4">
      {/* Ownership */}
      {ownership && ownership !== 'Unknown' && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="data-label">Ownership</span>
          </div>
          <p className="text-sm text-foreground pl-5">
            {ownership}
            {isGovernment && (
              <span className="text-xs text-warning ml-2 italic">
                (Check for industry capture)
              </span>
            )}
            {isAcademic && (
              <span className="text-xs text-muted-foreground ml-2 italic">
                (Academic Institution)
              </span>
            )}
          </p>
        </div>
      )}

      {/* Funding Sources */}
      {fundingSources.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Coins className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="data-label">Funding Sources</span>
          </div>
          <ul className="text-sm text-foreground pl-5 space-y-1">
            {fundingSources.map((source, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-muted-foreground">—</span>
                <span>{source}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Funding Transparency */}
      {fundingTransparency && fundingTransparency !== 'unknown' && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Eye className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="data-label">Funding Transparency</span>
          </div>
          <p className={cn(
            "text-sm font-semibold pl-5 font-mono",
            getTransparencyColor(fundingTransparency)
          )}>
            {getTransparencyLabel(fundingTransparency)}
          </p>
        </div>
      )}

      {/* Industry Ties */}
      {industryTies.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <Link2 className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="data-label">Industry Ties</span>
          </div>
          <p className="text-sm text-foreground pl-5">
            {industryTies.join(', ')}
          </p>
        </div>
      )}

      {/* Conflicts of Interest */}
      {conflictsOfInterest.length > 0 && (
        <div className="mt-3 border-l-2 border-danger bg-danger-muted pl-3 py-2">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-3.5 w-3.5 text-danger" />
            <span className="text-xs font-semibold uppercase tracking-wider text-danger">
              Conflicts of Interest
            </span>
          </div>
          <ul className="text-sm text-foreground space-y-1">
            {conflictsOfInterest.map((conflict, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-muted-foreground">•</span>
                <span>{conflict}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Academic/Government Warnings */}
      {(isAcademic && fundingSources.length === 0) && (
        <div className="border-l-2 border-warning bg-warning-muted pl-3 py-2">
          <p className="text-xs text-foreground">
            <span className="font-semibold">Note:</span> Universities often receive corporate research grants. 
            Specific funding for this article may not be disclosed.
          </p>
        </div>
      )}

      {isGovernment && (
        <div className="border-l-2 border-warning bg-warning-muted pl-3 py-2">
          <p className="text-xs text-foreground">
            <span className="font-semibold">Note:</span> Government agencies may be influenced by industry lobbying 
            and regulatory capture. Verify independence.
          </p>
        </div>
      )}
    </div>
  );
}
