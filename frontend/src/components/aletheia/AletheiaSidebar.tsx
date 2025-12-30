import { useState } from "react";
import { AletheiaHeader } from "./AletheiaHeader";
import { ArticleInfo } from "./ArticleInfo";
import { ClaimClassification } from "./ClaimClassification";
import { CredibilityScore } from "./CredibilityScore";
import { FundingInfo } from "./FundingInfo";
import { FlagList } from "./FlagList";
import { SourceComparison } from "./SourceComparison";
import { WarningBanner } from "./WarningBanner";
import { MythDetection } from "./MythDetection";
import { MissingContext } from "./MissingContext";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { CollapsibleSection } from "./CollapsibleSection";
import { MultiDimensionalAnalysis } from "./MultiDimensionalAnalysis";
import { 
  FileText, 
  FlaskConical, 
  BarChart3, 
  Coins, 
  Flag, 
  Search, 
  AlertTriangle, 
  Info,
  Scan
} from "lucide-react";
import { Button } from "@/components/ui/button";

// Type definitions for the analysis data
interface Publication {
  name?: string;
  domain: string;
  credibility_score?: number;
  credibility_explanation?: string;
  ownership?: string;
  funding_sources?: string[];
  conflicts_of_interest?: string[];
  industry_ties?: string[];
  funding_transparency?: string;
  red_flags?: string[];
  green_flags?: string[];
}

interface Evidence {
  label?: string;
  publication?: Publication;
  article?: {
    url: string;
    title: string;
  };
}

interface Analysis {
  warning?: string;
  recommendation?: string;
  funding_diversity?: number;
}

interface ClaimClass {
  classification: string;
  warning?: string;
  red_flags?: string[];
}

interface Myth {
  myth: string;
  reality: string;
}

interface AnalysisData {
  main_publication?: Publication;
  claim_classification?: ClaimClass;
  evidence?: Evidence;
  analysis?: Analysis;
  myths?: Myth[];
  missing_context?: string[];
  multi_dimensional_analysis?: {
    funding_independence_score?: number;
    research_support_pattern?: {
      pattern: string;
      description: string;
    };
    source_quality_score?: number;
    debate_status?: string;
    debate_description?: string;
    claims?: Array<{
      claim: string;
      type: string;
      supporting_count?: number;
      contradicting_count?: number;
      evidence_pattern?: string;
    }>;
    recommendation?: string;
  };
}

interface LoadingStep {
  message: string;
  submessage?: string;
  completed?: boolean;
}

interface AletheiaSidebarProps {
  isLoading?: boolean;
  loadingSteps?: LoadingStep[];
  currentLoadingStep?: number;
  articleTitle?: string;
  articleUrl?: string;
  data?: AnalysisData;
  onRefresh?: () => void;
  onScan?: () => void;
}

export function AletheiaSidebar({
  isLoading = false,
  loadingSteps = [],
  currentLoadingStep = 0,
  articleTitle,
  articleUrl,
  data,
  onRefresh,
  onScan
}: AletheiaSidebarProps) {
  const publication = data?.main_publication;
  const articleSource = articleUrl ? new URL(articleUrl).hostname : '';

  // Determine if source is academic or government
  const isAcademic = publication?.ownership?.toLowerCase().includes('university') || 
                     publication?.ownership?.toLowerCase().includes('college') ||
                     publication?.domain?.includes('.edu');

  const isGovernment = publication?.ownership?.toLowerCase().includes('department of') ||
                       publication?.ownership?.toLowerCase().includes('agency') ||
                       ['cdc', 'fda', 'nih', 'usda'].some(g => 
                         publication?.ownership?.toLowerCase().includes(g)
                       ) ||
                       publication?.domain?.includes('.gov');

  if (isLoading) {
    return (
      <div className="sidebar-width min-h-screen bg-background flex flex-col">
        <AletheiaHeader isLoading />
        <LoadingSkeleton steps={loadingSteps} currentStep={currentLoadingStep} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="sidebar-width min-h-screen bg-background flex flex-col">
        <AletheiaHeader onRefresh={onRefresh} />
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center space-y-4">
            <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center">
              <Search className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">No Article Selected</p>
              <p className="text-xs text-muted-foreground mt-1">
                Click the Aletheia icon on any health article to analyze it.
              </p>
            </div>
            {onScan && (
              <Button
                onClick={onScan}
                variant="outline"
                size="sm"
                className="mt-4"
              >
                <Scan className="h-4 w-4 mr-2" />
                Scan Current Page
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="sidebar-width min-h-screen bg-background flex flex-col">
      <AletheiaHeader onRefresh={onRefresh} isLoading={isLoading} />
      
      <div className="flex-1 overflow-y-auto">
        {/* Article Info */}
        {articleTitle && (
          <div className="px-4 py-4 border-b border-border">
            <ArticleInfo 
              title={articleTitle} 
              source={articleSource}
              url={articleUrl}
            />
          </div>
        )}

        {/* Claim Classification */}
        {data.claim_classification && (
          <div className="px-4 py-4 border-b border-border">
            <div className="flex items-center gap-2 mb-3">
              <FlaskConical className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Claim Classification
              </span>
            </div>
            <ClaimClassification
              classification={data.claim_classification.classification}
              warning={data.claim_classification.warning}
              redFlags={data.claim_classification.red_flags}
            />
          </div>
        )}

        {/* Source Credibility */}
        {publication && (
          <div className="px-4 py-4 border-b border-border">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Source Credibility
              </span>
            </div>
            {data.multi_dimensional_analysis ? (
              <MultiDimensionalAnalysis
                funding_independence_score={data.multi_dimensional_analysis.funding_independence_score}
                research_support_pattern={data.multi_dimensional_analysis.research_support_pattern}
                source_quality_score={data.multi_dimensional_analysis.source_quality_score}
                debate_status={data.multi_dimensional_analysis.debate_status}
                debate_description={data.multi_dimensional_analysis.debate_description}
                claims={data.multi_dimensional_analysis.claims}
                recommendation={data.multi_dimensional_analysis.recommendation}
              />
            ) : (
              <CredibilityScore
                score={publication.credibility_score || 0}
                name={publication.name || publication.domain}
                explanation={publication.credibility_explanation}
              />
            )}
          </div>
        )}

        {/* Collapsible Sections */}
        <div className="px-4">
          {/* Funding & Conflicts */}
          {publication && (
            <CollapsibleSection
              title="Funding & Conflicts"
              icon={<Coins className="h-4 w-4 text-muted-foreground" />}
            >
              <FundingInfo
                ownership={publication.ownership}
                fundingSources={publication.funding_sources}
                conflictsOfInterest={publication.conflicts_of_interest}
                industryTies={publication.industry_ties}
                fundingTransparency={publication.funding_transparency}
                isAcademic={isAcademic}
                isGovernment={isGovernment}
              />
            </CollapsibleSection>
          )}

          {/* Credibility Indicators */}
          {publication && (publication.red_flags?.length || publication.green_flags?.length) && (
            <CollapsibleSection
              title="Credibility Indicators"
              icon={<Flag className="h-4 w-4 text-muted-foreground" />}
            >
              <FlagList
                redFlags={publication.red_flags}
                greenFlags={publication.green_flags}
              />
            </CollapsibleSection>
          )}

          {/* Evidence Comparison */}
          {data.evidence?.publication && (
            <CollapsibleSection
              title="Counter-Perspective"
              icon={<Search className="h-4 w-4 text-muted-foreground" />}
            >
              <SourceComparison
                mainSource={{
                  name: publication?.name || publication?.domain || 'Main Source',
                  score: publication?.credibility_score || 0,
                  multiDimensionalScores: data.multi_dimensional_analysis ? {
                    funding_independence_score: data.multi_dimensional_analysis.funding_independence_score,
                    research_support_pattern: data.multi_dimensional_analysis.research_support_pattern,
                    source_quality_score: data.multi_dimensional_analysis.source_quality_score
                  } : undefined
                }}
                evidenceSource={{
                  name: data.evidence.publication.name || data.evidence.publication.domain,
                  score: data.evidence.publication.credibility_score || 0,
                  url: data.evidence.article?.url,
                  title: data.evidence.article?.title,
                  fundingSources: data.evidence.publication.funding_sources,
                  multiDimensionalScores: data.evidence.multi_dimensional_scores ? {
                    funding_independence_score: data.evidence.multi_dimensional_scores.funding_independence_score,
                    research_support_pattern: data.evidence.multi_dimensional_scores.research_support_pattern,
                    source_quality_score: data.evidence.multi_dimensional_scores.source_quality_score
                  } : undefined
                }}
                label={data.evidence.label}
                fundingDiversity={data.analysis?.funding_diversity}
              />
            </CollapsibleSection>
          )}

          {/* Myth Detection */}
          {data.myths && data.myths.length > 0 && (
            <CollapsibleSection
              title="Known Health Myths"
              icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
            >
              <MythDetection myths={data.myths} />
            </CollapsibleSection>
          )}

          {/* Missing Context */}
          {data.missing_context && data.missing_context.length > 0 && (
            <CollapsibleSection
              title="Missing Context"
              icon={<Info className="h-4 w-4 text-muted-foreground" />}
              defaultOpen={false}
            >
              <MissingContext items={data.missing_context} />
            </CollapsibleSection>
          )}
        </div>

        {/* Analysis Warning */}
        {data.analysis?.warning && (
          <div className="px-4 py-4">
            <WarningBanner
              warning={data.analysis.warning}
              recommendation={data.analysis.recommendation}
            />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border bg-card">
        <Button
          variant="outline"
          size="sm"
          className="w-full h-9 text-xs font-medium"
          onClick={onRefresh}
        >
          Analyze Another Article
        </Button>
      </div>
    </div>
  );
}
