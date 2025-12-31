import React from 'react';
import { AlertCircle, TrendingDown, Users, DollarSign, AlertTriangle } from 'lucide-react';

interface RedFlag {
  type: string;
  source?: string;
  concern?: string;
  evidence?: string;
}

interface FundingAnalysis {
  main_source_conflicts: RedFlag[];
  corroboration_conflicts: RedFlag[];
  all_sources_same_funder: boolean;
  industry_capture_signals: string[];
  funding_chain_integrity: 'HIGH' | 'COMPROMISED' | 'QUESTIONABLE' | 'INDEPENDENT' | 'UNKNOWN';
}

interface Source {
  title: string;
  url: string;
  domain: string;
  credibility_marker: string;
  snippet: string;
}

interface DissentAnalysis {
  dissenting_sources_found: boolean;
  source_count: number;
  sources: Source[];
  assessment: string;
}

interface ConsensusAnalysis {
  consensus_age_years?: number;
  evidence_strength_at_consensus?: string;
  evidence_changed_since_consensus?: string;
  red_flags: string[];
  integrity_assessment?: string;
  summary?: string;
}

interface RegulatoryAnalysis {
  regulatory_body: string;
  industry_type: string;
  capture_risk: 'HIGH' | 'MODERATE' | 'LOW' | 'UNKNOWN';
  signals_detected: number;
  signals: any[];
  note: string;
}

interface HistoricalPatterns {
  pattern_found: boolean;
  matches: Array<{
    historical_case: string;
    timeline: any;
    pattern: string;
  }>;
  warning?: string;
}

interface CaptureAnalysis {
  claim: string;
  funding_integrity: FundingAnalysis;
  dissenting_expertise: DissentAnalysis;
  consensus_integrity: ConsensusAnalysis;
  regulatory_capture: RegulatoryAnalysis | null;
  historical_patterns: HistoricalPatterns;
  dissent_authenticity: {
    authentic_dissent_count: number;
    manufactured_doubt_count: number;
    assessment: string;
  };
  overall_integrity_score: number;
  red_flags_summary: string[];
}

interface InstitutionalCaptureAnalysisProps {
  analysis?: CaptureAnalysis;
}

export function InstitutionalCaptureAnalysis({ analysis }: InstitutionalCaptureAnalysisProps) {
  if (!analysis) return null;

  const integrityScore = analysis.overall_integrity_score || 0;
  const integrityColor = 
    integrityScore >= 7 ? 'text-green-600' : 
    integrityScore >= 5 ? 'text-yellow-600' : 
    'text-red-600';

  const integrityBg = 
    integrityScore >= 7 ? 'bg-green-50' : 
    integrityScore >= 5 ? 'bg-yellow-50' : 
    'bg-red-50';

  return (
    <div className="space-y-4">
      {/* Overall Integrity Score */}
      <div className={`rounded-lg p-4 ${integrityBg} border border-gray-200`}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-gray-900">Institutional Integrity Assessment</h4>
          <div className={`text-2xl font-bold ${integrityColor}`}>
            {integrityScore.toFixed(1)}/10
          </div>
        </div>
        <p className="text-xs text-gray-600">
          {integrityScore >= 7 ? '✓ Appears independent of capture signals' : 
           integrityScore >= 5 ? '⚠ Some institutional concerns detected' : 
           '🚩 Significant integrity concerns - verify independently'}
        </p>
      </div>

      {/* Red Flags Summary */}
      {analysis.red_flags_summary && analysis.red_flags_summary.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            Detected Issues
          </h4>
          <div className="space-y-1">
            {analysis.red_flags_summary.map((flag, idx) => (
              <div key={idx} className="text-xs bg-red-50 border border-red-200 rounded p-2 text-red-800">
                {flag}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Funding Chain Analysis */}
      {analysis.funding_integrity && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-blue-600" />
            Funding Integrity
          </h4>
          <div className={`text-xs rounded p-2 ${
            analysis.funding_integrity.funding_chain_integrity === 'INDEPENDENT' 
              ? 'bg-green-50 border border-green-200 text-green-800' 
              : analysis.funding_integrity.funding_chain_integrity === 'COMPROMISED'
              ? 'bg-red-50 border border-red-200 text-red-800'
              : 'bg-yellow-50 border border-yellow-200 text-yellow-800'
          }`}>
            Status: <span className="font-semibold">{analysis.funding_integrity.funding_chain_integrity}</span>
          </div>
          
          {analysis.funding_integrity.main_source_conflicts.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold text-gray-700">Funding Conflicts:</p>
              {analysis.funding_integrity.main_source_conflicts.map((conflict, idx) => (
                <div key={idx} className="text-xs bg-gray-50 border border-gray-200 rounded p-2">
                  <span className="font-semibold text-red-700">{conflict.type}</span>
                  <p className="text-gray-600 mt-0.5">{conflict.concern}</p>
                </div>
              ))}
            </div>
          )}

          {analysis.funding_integrity.all_sources_same_funder && (
            <div className="text-xs bg-orange-50 border border-orange-200 rounded p-2 text-orange-800">
              ⚠️ All corroborating sources from same funder - potential echo chamber
            </div>
          )}
        </div>
      )}

      {/* Historical Patterns */}
      {analysis.historical_patterns?.pattern_found && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-purple-600" />
            Historical Patterns
          </h4>
          {analysis.historical_patterns.matches.map((match, idx) => (
            <div key={idx} className="text-xs bg-purple-50 border border-purple-200 rounded p-2">
              <p className="font-semibold text-purple-900">{match.historical_case}</p>
              <p className="text-purple-800 mt-0.5 text-xs">{match.pattern}</p>
            </div>
          ))}
          <p className="text-xs text-purple-700 italic">
            {analysis.historical_patterns.warning}
          </p>
        </div>
      )}

      {/* Credible Dissent */}
      {analysis.dissenting_expertise?.dissenting_sources_found && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-600" />
            Credible Dissenting Expertise
          </h4>
          <p className="text-xs text-gray-600">{analysis.dissenting_expertise.assessment}</p>
          {analysis.dissenting_expertise.sources.slice(0, 2).map((source, idx) => (
            <div key={idx} className="text-xs bg-blue-50 border border-blue-200 rounded p-2">
              <p className="font-semibold text-blue-900">{source.title}</p>
              <p className="text-blue-700 text-xs mt-1">{source.snippet}</p>
              <a 
                href={source.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 underline text-xs mt-1 inline-block"
              >
                Read more →
              </a>
            </div>
          ))}
        </div>
      )}

      {/* Consensus Integrity */}
      {analysis.consensus_integrity && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-indigo-600" />
            Consensus Formation
          </h4>
          <div className="text-xs space-y-1">
            {analysis.consensus_integrity.summary && (
              <p className="bg-indigo-50 border border-indigo-200 rounded p-2 text-indigo-800">
                {analysis.consensus_integrity.summary}
              </p>
            )}
            {analysis.consensus_integrity.red_flags?.map((flag, idx) => (
              <p key={idx} className="bg-orange-50 border border-orange-200 rounded p-2 text-orange-800">
                ⚠️ {flag}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Regulatory Capture */}
      {analysis.regulatory_capture && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            Regulatory Capture Risk
          </h4>
          <div className={`text-xs rounded p-2 ${
            analysis.regulatory_capture.capture_risk === 'HIGH' 
              ? 'bg-red-50 border border-red-200 text-red-800' 
              : analysis.regulatory_capture.capture_risk === 'MODERATE'
              ? 'bg-yellow-50 border border-yellow-200 text-yellow-800'
              : 'bg-green-50 border border-green-200 text-green-800'
          }`}>
            <span className="font-semibold">{analysis.regulatory_capture.regulatory_body}</span>: 
            <span className="font-semibold ml-1">{analysis.regulatory_capture.capture_risk}</span> Risk
          </div>
          {analysis.regulatory_capture.signals_detected > 0 && (
            <p className="text-xs text-gray-600">
              {analysis.regulatory_capture.signals_detected} capture signals detected
            </p>
          )}
        </div>
      )}

      {/* Dissent Authenticity */}
      {analysis.dissent_authenticity && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-900">Dissent Authenticity</h4>
          <p className="text-xs text-gray-600">{analysis.dissent_authenticity.assessment}</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="text-xs bg-blue-50 border border-blue-200 rounded p-2">
              <p className="font-semibold text-blue-900">Authentic</p>
              <p className="text-blue-700">{analysis.dissent_authenticity.authentic_dissent_count} sources</p>
            </div>
            <div className="text-xs bg-orange-50 border border-orange-200 rounded p-2">
              <p className="font-semibold text-orange-900">Questionable</p>
              <p className="text-orange-700">{analysis.dissent_authenticity.manufactured_doubt_count} sources</p>
            </div>
          </div>
        </div>
      )}

      <div className="text-xs text-gray-500 italic p-2 bg-gray-50 rounded border border-gray-200">
        💡 This analysis flags potential institutional capture, funding conflicts, and dissenting expertise. 
        Not all flags indicate deception - some indicate legitimate scientific debate. Follow money flows and 
        check credentials independently.
      </div>
    </div>
  );
}
