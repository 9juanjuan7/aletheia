"""
Comprehensive credibility framework analyzer based on evidence-based evaluation model.

Implements 6-dimension evaluation:
1. Provenance & Authority (who made it, credentials, track record, funding)
2. Evidence & Methodology (methods, data sources, primary sources)
3. Accuracy & Consistency (internal/external consistency, errors)
4. Transparency & Accountability (conflicts, editorial process, corrections)
5. Tone & Rhetoric (emotional language, persuasion vs evidence)
6. Timeliness & Recency (current? superseded? version history?)

Plus:
- Source type classification (primary/secondary)
- Independence verification (corroboration)
- Systematic red flags
- Confidence calibration
"""

from groq import Groq
import os
from datetime import datetime

client = Groq(api_key=os.getenv('GROQ_API_KEY'))


class CredibilityFrameworkAnalyzer:
    """
    Evaluates source credibility across 6 dimensions + red flags.
    Returns comprehensive credibility profile.
    """
    
    def __init__(self):
        self.red_flags = {
            'provenance': [
                'anonymous authorship',
                'no institutional affiliation',
                'no verifiable author trace',
                'unrevealed funding sources'
            ],
            'evidence': [
                'no access to primary evidence',
                'reliance on hearsay',
                'selective quoting',
                'no data sources cited',
                'screenshots as evidence'
            ],
            'accuracy': [
                'repeated factual errors',
                'unaddressed corrections',
                'logical leaps',
                'misquotations'
            ],
            'transparency': [
                'undisclosed conflicts of interest',
                'no editorial process visible',
                'no corrections published',
                'no accountability mechanism'
            ],
            'rhetoric': [
                'excessive emotional language',
                'hyperbole',
                'conspiracy language',
                '"doctors hate this"',
                '"miracle" or "cure"',
                'all-or-nothing thinking'
            ],
            'citations': [
                'circular citation networks',
                'single source echo chamber',
                'unverified citations',
                'reputation laundering'
            ]
        }
    
    def classify_source_type(self, source_data: dict) -> dict:
        """
        Classify whether source is primary, secondary, tertiary, or unclassified.
        
        Primary: peer-reviewed studies, official datasets, court records, raw data
        Secondary: reviews, news articles citing sources, systematic reviews
        Tertiary: encyclopedias, health blogs summarizing research
        """
        
        domain = source_data.get('domain', '').lower()
        name = source_data.get('name', '').lower()
        green_flags = source_data.get('green_flags', [])
        
        is_academic = '.edu' in domain or 'university' in name
        is_gov = '.gov' in domain or 'government' in name
        is_peer_reviewed = any('peer' in f.lower() for f in green_flags)
        is_journal = any(j in domain for j in ['pubmed', 'ncbi.nlm', 'nature.com', 'science.org', 'thelancet', 'jama'])
        
        is_news = any(n in domain for n in ['cnn', 'bbc', 'reuters', 'associated press', 'nytimes'])
        is_blog = any(b in domain for b in ['wordpress', 'medium', 'substack', 'blogger', '.blogspot'])
        
        if is_peer_reviewed or is_journal or (is_academic and 'study' in name):
            return {
                'type': 'PRIMARY',
                'description': 'Peer-reviewed research or official dataset',
                'confidence_weight': 1.0  # Highest weight in corroboration
            }
        elif is_news and is_academic:
            return {
                'type': 'SECONDARY',
                'description': 'News reporting on research with cited sources',
                'confidence_weight': 0.8
            }
        elif is_gov:
            return {
                'type': 'PRIMARY',
                'description': 'Official government dataset or statistics',
                'confidence_weight': 1.0
            }
        elif is_news:
            return {
                'type': 'SECONDARY',
                'description': 'News article (verify sources cited)',
                'confidence_weight': 0.7
            }
        elif is_blog:
            return {
                'type': 'TERTIARY',
                'description': 'Blog or aggregate summary (check primary sources)',
                'confidence_weight': 0.4
            }
        else:
            return {
                'type': 'UNCLASSIFIED',
                'description': 'Unable to determine source type',
                'confidence_weight': 0.5
            }
    
    def analyze_tone_and_rhetoric(self, title: str, content: str = "") -> dict:
        """
        Use GPT to detect emotional language, hyperbole, persuasion tactics.
        """
        
        prompt = f"""Analyze this health article for problematic rhetoric and tone.

Title: {title}
{f'Content (first 500 chars): {content[:500]}' if content else ''}

Identify:
1. Emotional language (e.g., "shocking", "dangerous", "cure")
2. Hyperbole ("never", "always", "miraculous")
3. Conspiracy thinking ("they don't want you to know", "doctors hate")
4. Fear-mongering
5. Cherry-picking language ("some studies show" vs "research shows")
6. Trustworthy language (neutral, acknowledges limitations, cites sources)

Return JSON:
{{
  "tone_score": <0-10, higher = more trustworthy>,
  "red_flag_rhetoric": [<specific problematic phrases>],
  "confidence_indicators": [<evidence of careful language>],
  "summary": "<one sentence assessment>"
}}"""
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"⚠️ Tone analysis failed: {e}")
            return {
                'tone_score': 5.0,
                'red_flag_rhetoric': [],
                'confidence_indicators': [],
                'summary': 'Unable to analyze tone'
            }
    
    def check_systematic_red_flags(self, source_data: dict) -> dict:
        """
        Check against systematic red flags from the framework.
        Returns which red flags are present.
        """
        
        detected_flags = {
            'provenance': [],
            'evidence': [],
            'accuracy': [],
            'transparency': [],
            'rhetoric': [],
            'citations': []
        }
        
        # Provenance checks
        if not source_data.get('name') or source_data.get('name') == 'Unknown':
            detected_flags['provenance'].append('anonymous authorship')
        
        if not source_data.get('ownership'):
            detected_flags['provenance'].append('no institutional affiliation')
        
        conflicts = source_data.get('conflicts_of_interest', [])
        if not conflicts and source_data.get('funding_transparency', '').lower() == 'none':
            detected_flags['provenance'].append('unrevealed funding sources')
        
        # Evidence checks
        red_flags = source_data.get('red_flags', [])
        if any('no citation' in f.lower() for f in red_flags):
            detected_flags['evidence'].append('no access to primary evidence')
        
        if any('unverified' in f.lower() for f in red_flags):
            detected_flags['evidence'].append('unverified claims')
        
        # Transparency checks
        if not source_data.get('funding_sources') and not conflicts:
            detected_flags['transparency'].append('undisclosed conflicts')
        
        # Calculate severity
        total_flags = sum(len(v) for v in detected_flags.values())
        severity = min(10, total_flags * 1.5)  # Each flag reduces trust
        
        return {
            'detected_flags': detected_flags,
            'total_red_flags': total_flags,
            'severity_score': severity,  # 0-10, higher = more concerning
            'has_critical_flags': total_flags >= 3
        }
    
    def assess_recency(self, publication_date: str = None) -> dict:
        """
        Check if source is current, outdated, or superseded.
        """
        
        if not publication_date:
            return {
                'status': 'UNKNOWN',
                'age_years': None,
                'concern': 'No publication date found',
                'recency_penalty': 0.2
            }
        
        try:
            # Try to parse date
            from datetime import datetime
            pub_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
            age = (datetime.now() - pub_date.replace(tzinfo=None)).days / 365.25
            
            if age < 2:
                return {
                    'status': 'CURRENT',
                    'age_years': age,
                    'concern': None,
                    'recency_penalty': 0.0
                }
            elif age < 5:
                return {
                    'status': 'RECENT',
                    'age_years': age,
                    'concern': 'Information may be outdated',
                    'recency_penalty': 0.1
                }
            elif age < 10:
                return {
                    'status': 'AGING',
                    'age_years': age,
                    'concern': 'Research may have advanced significantly',
                    'recency_penalty': 0.2
                }
            else:
                return {
                    'status': 'OUTDATED',
                    'age_years': age,
                    'concern': 'Likely superseded by newer research',
                    'recency_penalty': 0.4
                }
        except:
            return {
                'status': 'UNPARSEABLE',
                'age_years': None,
                'concern': 'Could not parse publication date',
                'recency_penalty': 0.1
            }
    
    def verify_independence(self, main_source: dict, corroborating_sources: list) -> dict:
        """
        Check if corroborating sources are truly independent.
        
        Red flags:
        - All sources citing same study
        - All from same institution
        - Press release pattern (source A cites B, B cites A, both cite press release)
        """
        
        if not corroborating_sources:
            return {
                'is_independent': False,
                'independence_score': 0.0,
                'concerns': ['No corroborating sources found'],
                'recommendation': 'Single source is insufficient for important claims'
            }
        
        # Check source diversity
        institutions = set()
        countries = set()
        methodologies = set()
        
        for source in corroborating_sources:
            if source.get('ownership'):
                institutions.add(source['ownership'])
            if source.get('domain'):
                # Simple country detection from domain
                if '.uk' in source['domain']:
                    countries.add('UK')
                elif '.de' in source['domain']:
                    countries.add('Germany')
                elif '.au' in source['domain']:
                    countries.add('Australia')
                else:
                    countries.add('Other')
        
        # Diversity scoring
        source_count = len(corroborating_sources)
        unique_institutions = len(institutions)
        unique_countries = len(countries)
        
        independence_score = (
            (min(unique_institutions, 3) / 3) * 0.5 +
            (min(unique_countries, 2) / 2) * 0.3 +
            (min(source_count, 5) / 5) * 0.2
        ) * 10
        
        concerns = []
        if unique_institutions < 2:
            concerns.append('Corroboration from single institution only')
        if source_count < 2:
            concerns.append('Insufficient number of corroborating sources')
        
        return {
            'is_independent': independence_score >= 6.0,
            'independence_score': independence_score,
            'unique_institutions': unique_institutions,
            'unique_countries': unique_countries,
            'source_count': source_count,
            'concerns': concerns if concerns else None,
            'recommendation': 'Independent corroboration detected' if independence_score >= 6 else 'Sources lack sufficient independence'
        }
    
    def comprehensive_evaluation(self, source_data: dict, article_title: str, 
                                article_content: str = "", corroborating_sources: list = None) -> dict:
        """
        Perform complete credibility evaluation across all dimensions.
        """
        
        print(f"\n📋 Comprehensive Credibility Evaluation: {source_data.get('name', 'Unknown')}")
        
        # 1. Source type
        source_type = self.classify_source_type(source_data)
        print(f"  → Source type: {source_type['type']}")
        
        # 2. Red flags
        red_flags = self.check_systematic_red_flags(source_data)
        print(f"  → Red flags detected: {red_flags['total_red_flags']}")
        
        # 3. Tone & rhetoric
        tone = self.analyze_tone_and_rhetoric(article_title, article_content)
        print(f"  → Tone score: {tone['tone_score']}/10")
        
        # 4. Recency
        recency = self.assess_recency(source_data.get('publication_date'))
        print(f"  → Recency: {recency['status']}")
        
        # 5. Independence
        independence = self.verify_independence(
            source_data,
            corroborating_sources or []
        )
        print(f"  → Independence score: {independence['independence_score']:.1f}/10")
        
        # 6. Existing scores (keep what works)
        funding_score = source_data.get('credibility_score', 5.0)  # Will be replaced by funding independence
        quality_score = source_data.get('credibility_score', 5.0)  # Will be replaced by source quality
        
        return {
            'source_name': source_data.get('name', 'Unknown'),
            'source_domain': source_data.get('domain', 'Unknown'),
            
            'source_type': source_type,
            'red_flags': red_flags,
            'tone_analysis': tone,
            'recency': recency,
            'independence_verification': independence,
            
            'credibility_profile': {
                'provenance_authority': self._calculate_provenance_score(source_data),
                'evidence_methodology': self._calculate_evidence_score(source_data),
                'accuracy_consistency': self._calculate_accuracy_score(source_data),
                'transparency_accountability': self._calculate_transparency_score(source_data),
                'tone_rhetoric': tone['tone_score'],
                'timeliness': 10.0 - recency['recency_penalty'] * 10
            },
            
            'overall_credibility_assessment': self._generate_assessment(
                red_flags, tone, recency, independence, source_type
            )
        }
    
    def _calculate_provenance_score(self, source_data: dict) -> float:
        """Score provenance based on credentials, track record, funding."""
        score = 5.0
        
        if source_data.get('ownership'):
            if any(x in source_data['ownership'].lower() for x in ['university', 'government', 'nonprofit']):
                score += 2.0
            elif any(x in source_data['ownership'].lower() for x in ['pharma', 'marketing', 'ad']):
                score -= 2.0
        
        funding = source_data.get('funding_sources', [])
        if funding:
            score += 1.0
        
        return max(0, min(10, score))
    
    def _calculate_evidence_score(self, source_data: dict) -> float:
        """Score evidence methodology based on primary sources, data access."""
        score = 5.0
        
        green_flags = source_data.get('green_flags', [])
        red_flags = source_data.get('red_flags', [])
        
        for flag in green_flags:
            if any(x in flag.lower() for x in ['peer-reviewed', 'study', 'citation', 'primary']):
                score += 1.5
        
        for flag in red_flags:
            if any(x in flag.lower() for x in ['no citation', 'missing', 'unverified']):
                score -= 1.5
        
        return max(0, min(10, score))
    
    def _calculate_accuracy_score(self, source_data: dict) -> float:
        """Score accuracy based on consistency, errors, corrections."""
        score = 5.0
        
        red_flags = source_data.get('red_flags', [])
        for flag in red_flags:
            if any(x in flag.lower() for x in ['error', 'inconsistent', 'retraction']):
                score -= 2.0
        
        return max(0, min(10, score))
    
    def _calculate_transparency_score(self, source_data: dict) -> float:
        """Score transparency based on disclosures, editorial process, corrections."""
        score = 5.0
        
        if source_data.get('conflicts_of_interest'):
            score += 1.5  # Points for transparency
        
        if source_data.get('funding_transparency') == 'high':
            score += 2.0
        elif source_data.get('funding_transparency') == 'low':
            score -= 1.5
        
        return max(0, min(10, score))
    
    def _generate_assessment(self, red_flags: dict, tone: dict, recency: dict, 
                           independence: dict, source_type: dict) -> str:
        """
        Generate overall assessment considering all factors.
        """
        
        concerns = []
        
        if red_flags['has_critical_flags']:
            concerns.append(f"{red_flags['total_red_flags']} critical red flags detected")
        
        if tone['tone_score'] < 4:
            concerns.append('Problematic rhetoric detected')
        
        if recency['status'] == 'OUTDATED':
            concerns.append('Information is significantly outdated')
        
        if not independence['is_independent']:
            concerns.append('Lacks independent corroboration')
        
        if source_type['type'] == 'TERTIARY':
            concerns.append('Tertiary source - verify primary sources')
        
        if not concerns:
            return f"✅ {source_type['type']} source with no major credibility concerns. Tone is trustworthy."
        else:
            return f"⚠️ {source_type['type']} source. Concerns: {'; '.join(concerns)}"
