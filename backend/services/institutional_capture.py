"""
Institutional Capture & Consensus Integrity Analyzer

Detects when:
- Research/consensus is driven by financial incentives
- Credible dissenting experts are being suppressed
- Regulatory bodies are captured by industries they regulate
- Consensus formed without evidence changing
- Alternative research is ignored
- Safety narratives collapse later (historical patterns)

NOT about conspiracy theories - about following money and tracking expertise.
"""

from groq import Groq
from services.searxng import SearxNGClient
import os
import json


class InstitutionalCaptureAnalyzer:
    """
    Analyzes whether consensus/research might be driven by institutional capture
    rather than evidence alone.
    """
    
    def __init__(self):
        # Lazy-load API clients
        self.client = None
        self.searxng_client = None
        
        # Known regulatory/industry relationships
        self.regulatory_bodies = {
            'FDA': ['pharmaceutical', 'food'],
            'CDC': ['pharmaceutical', 'vaccine'],
            'EPA': ['chemical', 'oil', 'agriculture'],
            'USDA': ['agriculture', 'livestock'],
            'FTC': ['advertising', 'marketing']
        }
        
        # Historical patterns of "safe until it wasn't"
        self.historical_reversals = {
            'asbestos': {'declared_safe': 1920, 'proven_harmful': 1970, 'banned': 1989},
            'tobacco': {'declared_safe': 1950, 'proven_harmful': 1964, 'acknowledged': 2000},
            'thalidomide': {'declared_safe': 1957, 'proven_harmful': 1962},
            'DDT': {'declared_safe': 1939, 'proven_harmful': 1970, 'banned': 1972},
            'hormone_replacement_therapy': {'peak_usage': 2000, 'reversed': 2002},
            'sugar_safety': {'consensus': 1950, 'questioned': 2010}
        }
    
    def _get_groq_client(self):
        """Lazy-load Groq client"""
        if not self.client:
            self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        return self.client
    
    def _get_searxng_client(self):
        """Lazy-load SearxNG client"""
        if not self.searxng_client:
            self.searxng_client = SearxNGClient()
        return self.searxng_client
    
    def detect_funding_chain_conflicts(self, main_source: dict, corroborating_sources: list = None) -> dict:
        """
        Trace funding to find conflicts of interest.
        Does the funder benefit from the conclusion?
        """
        
        print("\n💰 Analyzing Funding Chains...")
        
        conflicts = {
            'main_source_conflicts': [],
            'corroboration_conflicts': [],
            'all_sources_same_funder': False,
            'industry_capture_signals': [],
            'funding_chain_integrity': 'UNKNOWN'
        }
        
        main_funding = main_source.get('funding_sources', [])
        main_conflicts = main_source.get('conflicts_of_interest', [])
        
        # Analyze main source funding
        for funding in main_funding:
            funding_lower = funding.lower()
            
            # Check for direct conflicts
            if any(x in funding_lower for x in ['pharmaceutical', 'pharma', 'drug', 'manufacturer']):
                conflicts['main_source_conflicts'].append({
                    'type': 'PHARMA_FUNDED',
                    'source': funding,
                    'concern': 'Research funded by pharma company that profits from results'
                })
            
            if any(x in funding_lower for x in ['sugar', 'soda', 'corn', 'agricultural']):
                conflicts['main_source_conflicts'].append({
                    'type': 'INDUSTRY_FUNDED',
                    'source': funding,
                    'concern': 'Research funded by industry that profits from conclusions'
                })
            
            if any(x in funding_lower for x in ['advertising', 'marketing', 'pr']):
                conflicts['main_source_conflicts'].append({
                    'type': 'MARKETING_FUNDED',
                    'source': funding,
                    'concern': 'Funded by entity with interest in specific conclusion'
                })
        
        # Check for undisclosed conflicts
        if not main_funding and main_conflicts:
            conflicts['main_source_conflicts'].append({
                'type': 'UNDISCLOSED_CONFLICT',
                'source': 'Unknown',
                'concern': 'Conflicts present but funding sources not revealed'
            })
        
        # Analyze corroborating sources
        if corroborating_sources:
            all_funders = set()
            for source in corroborating_sources:
                funding = source.get('funding_sources', [])
                for f in funding:
                    all_funders.add(f.lower())
                
                # Check each source
                for funder in funding:
                    if any(x in funder.lower() for x in ['pharma', 'drug', 'manufacturer']):
                        conflicts['corroboration_conflicts'].append({
                            'source': source.get('name', 'Unknown'),
                            'funder': funder,
                            'concern': 'Corroboration from pharma-funded source'
                        })
            
            # Check if all trace to same source
            if len(all_funders) == 1:
                conflicts['all_sources_same_funder'] = True
                conflicts['industry_capture_signals'].append(
                    'All corroborating sources funded by same entity - potential echo chamber'
                )
        
        # Determine integrity
        if conflicts['main_source_conflicts']:
            conflicts['funding_chain_integrity'] = 'COMPROMISED'
        elif conflicts['all_sources_same_funder']:
            conflicts['funding_chain_integrity'] = 'QUESTIONABLE'
        else:
            conflicts['funding_chain_integrity'] = 'INDEPENDENT'
        
        print(f"  → Funding integrity: {conflicts['funding_chain_integrity']}")
        if conflicts['main_source_conflicts']:
            print(f"  → Conflicts found: {len(conflicts['main_source_conflicts'])}")
        
        return conflicts
    
    def find_credible_dissent(self, claim: str, consensus_position: str) -> dict:
        """
        Search for credible experts who disagree with consensus.
        Not fringe deniers - actual experts with credentials.
        """
        
        print("\n🔍 Searching for Credible Dissenting Expertise...")
        
        # Build search for dissenting experts
        search_query = f"{claim} alternative perspective credible experts disagree"
        
        try:
            searxng = self._get_searxng_client()
            response = searxng.search(
                query=search_query,
                max_results=5,
                search_depth="basic"
            )
            
            dissenting_sources = []
            for result in response.get('results', []):
                domain = result.get('url', '').lower()
                
                # Filter for credible sources only
                is_academic = '.edu' in domain or 'university' in result.get('title', '').lower()
                is_published = any(x in domain for x in ['pubmed', 'nature', 'science', 'journal'])
                has_credentials = any(x in result.get('content', '').lower() for x in ['phd', 'md', 'professor', 'research'])
                
                if is_academic or is_published or has_credentials:
                    dissenting_sources.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'domain': domain,
                        'credibility_marker': 'academic' if is_academic else 'published' if is_published else 'expert',
                        'snippet': result.get('content', '')[:200]
                    })
            
            return {
                'dissenting_sources_found': len(dissenting_sources) > 0,
                'source_count': len(dissenting_sources),
                'sources': dissenting_sources[:3],  # Top 3
                'assessment': self._assess_dissent_credibility(dissenting_sources)
            }
        
        except Exception as e:
            print(f"  ⚠️ Dissent search failed: {e}")
            return {
                'dissenting_sources_found': False,
                'source_count': 0,
                'sources': [],
                'assessment': 'Unable to search for dissenting expertise'
            }
    
    def _assess_dissent_credibility(self, sources: list) -> str:
        """Assess whether dissent is credible or fringe."""
        
        if not sources:
            return 'No credible dissenting expertise found'
        
        credible_count = sum(1 for s in sources if s.get('credibility_marker') in ['academic', 'published'])
        
        if credible_count >= 2:
            return 'Credible dissenting expertise exists with academic/peer-reviewed backing'
        elif credible_count == 1:
            return 'Limited credible dissent found - largely consensus'
        else:
            return 'Dissent found mostly from non-credible sources - consensus appears robust'
    
    def detect_consensus_integrity(self, claim: str, research_age_years: int = 0) -> dict:
        """
        Check: Did consensus form BECAUSE of evidence, or BEFORE examining evidence?
        
        Red flags:
        - Consensus unchanged despite new evidence
        - Consensus formed when evidence was weak
        - Consensus defended despite contrary evidence
        """
        
        print("\n📊 Analyzing Consensus Formation...")
        
        prompt = f"""Analyze the consensus around this health claim for signs of institutional capture or groupthink.

Claim: {claim}

Check for:
1. When did consensus form vs when evidence became strong?
2. Have contradictory findings been ignored or suppressed?
3. Is consensus defended more by authority than evidence?
4. Do financial incentives align with consensus?
5. Are dissenting credible experts present but marginalized?

Return JSON:
{{
  "consensus_age_years": <estimate>,
  "evidence_strength_at_consensus": "<weak/moderate/strong>",
  "evidence_changed_since_consensus": "<yes/no/unclear>",
  "red_flags": [<specific concerns>],
  "integrity_assessment": "<HIGH/MODERATE/LOW>",
  "summary": "<one sentence>"
}}"""
        
        try:
            client = self._get_groq_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            print(f"  ⚠️ Consensus analysis failed: {e}")
            return {
                'consensus_age_years': None,
                'evidence_strength_at_consensus': 'unknown',
                'evidence_changed_since_consensus': 'unknown',
                'red_flags': [],
                'integrity_assessment': 'UNKNOWN',
                'summary': 'Unable to assess consensus integrity'
            }
    
    def check_regulatory_capture(self, industry_type: str, regulatory_body: str = 'FDA') -> dict:
        """
        Check if regulatory body is captured by the industry it regulates.
        
        Signals:
        - Revolving door (regulators from industry, back to industry)
        - Advisory boards filled with industry
        - Approval rates unusually high
        """
        
        print(f"\n🏛️ Checking for Regulatory Capture ({regulatory_body})...")
        
        # Search for revolving door between regulator and industry
        search_query = f"{regulatory_body} {industry_type} revolving door former employees"
        
        try:
            searxng = self._get_searxng_client()
            response = searxng.search(
                query=search_query,
                max_results=3,
                search_depth="basic"
            )
            
            capture_signals = []
            
            for result in response.get('results', []):
                content = result.get('content', '').lower()
                
                if any(x in content for x in ['revolving door', 'former', 'employee', 'conflict']):
                    capture_signals.append({
                        'signal': 'Revolving door detected',
                        'source': result.get('title', ''),
                        'evidence': result.get('content', '')[:150]
                    })
            
            capture_risk = 'HIGH' if len(capture_signals) >= 2 else 'MODERATE' if capture_signals else 'LOW'
            
            return {
                'regulatory_body': regulatory_body,
                'industry_type': industry_type,
                'capture_risk': capture_risk,
                'signals_detected': len(capture_signals),
                'signals': capture_signals,
                'note': 'Check for: industry board members, fast-track approvals, advisory board composition'
            }
        
        except Exception as e:
            print(f"  ⚠️ Capture check failed: {e}")
            return {
                'regulatory_body': regulatory_body,
                'capture_risk': 'UNKNOWN',
                'signals_detected': 0,
                'signals': [],
                'note': 'Unable to assess'
            }
    
    def find_historical_pattern_match(self, claim_topic: str) -> dict:
        """
        Check if claim follows pattern of historical "safe until proven harmful" reversals.
        """
        
        print("\n📜 Checking Historical Patterns...")
        
        matches = []
        for historical_case, timeline in self.historical_reversals.items():
            if any(word in claim_topic.lower() for word in historical_case.lower().split('_')):
                matches.append({
                    'historical_case': historical_case.replace('_', ' ').title(),
                    'timeline': timeline,
                    'pattern': f"Consensus shifted {timeline.get('reversed', timeline.get('banned', 'N/A'))} years after initial claims of safety"
                })
        
        if matches:
            return {
                'pattern_found': True,
                'matches': matches,
                'warning': 'Similar topics have had consensus reversed in past - increased skepticism warranted'
            }
        else:
            return {
                'pattern_found': False,
                'matches': [],
                'warning': None
            }
    
    def detect_manufactured_doubt(self, dissenting_sources: list, main_funder: str = None) -> dict:
        """
        Distinguish between:
        1. Legitimate expertise disagreement (credible experts)
        2. Manufactured doubt (funded opposition to create fake debate)
        """
        
        print("\n🚩 Assessing Dissent Authenticity...")
        
        authentic_dissent = []
        manufactured_doubt = []
        
        for source in dissenting_sources:
            # If dissent is funded by competing industry, it's likely manufactured
            if main_funder:
                # Check if this source is funded by competitor
                funder = source.get('funding_source', '').lower()
                if funder and funder != main_funder.lower():
                    manufactured_doubt.append({
                        'source': source.get('title', ''),
                        'concern': f'Funded by competitor to {main_funder}',
                        'authenticity': 'QUESTIONABLE'
                    })
                else:
                    authentic_dissent.append(source)
            else:
                authentic_dissent.append(source)
        
        return {
            'authentic_dissent_count': len(authentic_dissent),
            'manufactured_doubt_count': len(manufactured_doubt),
            'authentic_sources': authentic_dissent[:2],
            'suspicious_sources': manufactured_doubt,
            'assessment': self._rate_dissent_authenticity(authentic_dissent, manufactured_doubt)
        }
    
    def _rate_dissent_authenticity(self, authentic: list, manufactured: list) -> str:
        """Rate whether dissent is real expertise or manufactured doubt."""
        
        if not authentic and not manufactured:
            return 'No credible dissent found'
        elif len(authentic) > len(manufactured):
            return 'Credible dissenting expertise appears independent'
        elif len(manufactured) >= len(authentic):
            return '⚠️ Much dissent appears funded to create doubt - be cautious'
        else:
            return 'Mixed dissent - some authentic, some manufactured'
    
    def comprehensive_capture_analysis(self, claim: str, main_source: dict, 
                                      corroborating_sources: list = None,
                                      industry_type: str = None) -> dict:
        """
        Complete institutional capture analysis.
        """
        
        print(f"\n{'='*60}")
        print(f"🔬 INSTITUTIONAL CAPTURE ANALYSIS")
        print(f"{'='*60}")
        
        # 1. Funding chains
        funding_analysis = self.detect_funding_chain_conflicts(main_source, corroborating_sources)
        
        # 2. Credible dissent
        dissent = self.find_credible_dissent(claim, main_source.get('name', 'Unknown'))
        
        # 3. Consensus integrity
        consensus = self.detect_consensus_integrity(claim)
        
        # 4. Regulatory capture (if applicable)
        regulatory = None
        if industry_type:
            regulatory = self.check_regulatory_capture(industry_type)
        
        # 5. Historical patterns
        historical = self.find_historical_pattern_match(claim)
        
        # 6. Manufactured doubt
        manufactured = self.detect_manufactured_doubt(dissent.get('sources', []))
        
        # Calculate overall integrity score
        integrity_score = self._calculate_integrity_score(
            funding_analysis, dissent, consensus, regulatory, historical
        )
        
        return {
            'claim': claim,
            'funding_integrity': funding_analysis,
            'dissenting_expertise': dissent,
            'consensus_integrity': consensus,
            'regulatory_capture': regulatory,
            'historical_patterns': historical,
            'dissent_authenticity': manufactured,
            'overall_integrity_score': integrity_score,
            'red_flags_summary': self._generate_red_flags_summary(
                funding_analysis, dissent, consensus, regulatory, historical
            )
        }
    
    def _calculate_integrity_score(self, funding, dissent, consensus, regulatory, historical) -> float:
        """
        Calculate how much we should trust the consensus/sources.
        0-10 scale, lower = more concerning.
        """
        
        score = 10.0
        
        # Funding issues
        if funding['funding_chain_integrity'] == 'COMPROMISED':
            score -= 3.0
        elif funding['funding_chain_integrity'] == 'QUESTIONABLE':
            score -= 1.5
        
        # Lack of credible dissent
        if not dissent['dissenting_sources_found']:
            score -= 0.5  # Slight concern if zero dissent
        
        # Consensus integrity issues
        if consensus.get('integrity_assessment') == 'LOW':
            score -= 3.0
        elif consensus.get('integrity_assessment') == 'MODERATE':
            score -= 1.5
        
        # Regulatory capture
        if regulatory and regulatory.get('capture_risk') == 'HIGH':
            score -= 2.5
        elif regulatory and regulatory.get('capture_risk') == 'MODERATE':
            score -= 1.0
        
        # Historical pattern match
        if historical['pattern_found']:
            score -= 1.5  # Extra skepticism warranted
        
        return max(0, min(10, score))
    
    def _generate_red_flags_summary(self, funding, dissent, consensus, regulatory, historical) -> list:
        """Generate list of specific concerns."""
        
        flags = []
        
        if funding['funding_chain_integrity'] == 'COMPROMISED':
            flags.append('⚠️ FUNDING CONFLICT: Research funded by entity with interest in outcome')
        
        if funding['all_sources_same_funder']:
            flags.append('⚠️ ECHO CHAMBER: All corroborating sources from same funder')
        
        if not dissent['dissenting_sources_found']:
            flags.append('⚠️ NO DISSENT: No credible experts questioning consensus')
        
        if consensus.get('red_flags'):
            for flag in consensus.get('red_flags', []):
                flags.append(f"⚠️ CONSENSUS: {flag}")
        
        if regulatory and regulatory.get('capture_risk') == 'HIGH':
            flags.append(f"⚠️ REGULATORY CAPTURE: {regulatory['regulatory_body']} potentially captured by industry")
        
        if historical['pattern_found']:
            flags.append(f"⚠️ HISTORICAL: Similar claims ({historical['matches'][0]['historical_case']}) reversed in past")
        
        return flags if flags else ['✅ No major red flags detected']
