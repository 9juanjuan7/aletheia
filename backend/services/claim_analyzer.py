import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime

load_dotenv()
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class ClaimAnalyzer:
    """
    Funding-aware claim classification system
    Prevents accepting industry narratives as "established facts"
    """
    
    def __init__(self):
        self.conflict_patterns = {
            'pharmaceutical': ['drug', 'medication', 'vaccine', 'treatment', 'prescription', 
                             'pharma', 'medicine', 'therapy', 'opioid', 'statin'],
            'food_industry': ['diet', 'nutrition', 'food', 'eating', 'sugar', 'fat', 
                            'carb', 'protein', 'breakfast', 'meal'],
            'supplement': ['vitamin', 'supplement', 'natural', 'herbal', 'remedy', 
                          'cure', 'detox', 'cleanse'],
            'tobacco': ['smoking', 'nicotine', 'tobacco', 'vaping', 'cigarette'],
            'dairy': ['milk', 'dairy', 'calcium', 'bone health', 'lactose'],
            'meat': ['protein', 'meat', 'animal', 'cholesterol', 'red meat'],
            'alcohol': ['alcohol', 'wine', 'beer', 'drinking', 'moderate consumption']
        }
        
        # Basic uncontroversial health facts
        self.basic_health_facts = [
            'vegetables', 'fruits', 'water', 'hydration', 'exercise', 'sleep',
            'hygiene', 'handwashing', 'smoking harmful', 'physical activity'
        ]
    
    def analyze_claim(self, title, article_content, main_pub):
        """
        Two-layer analysis:
        1. Surface claim classification (what it appears to be)
        2. Funding reality check (who's making the claim and why)
        """
        
        print(f"\n🔍 CLAIM ANALYSIS: {title[:60]}...")
        
        # Layer 1: Surface classification
        surface_class = self.classify_claim_surface(title, article_content)
        print(f"  📋 Surface classification: {surface_class['classification']}")
        
        # Layer 2: Funding reality check
        funding_check = self.funding_reality_check(title, main_pub, surface_class)
        print(f"  💰 Funding check: {funding_check['status']}")
        
        # Final classification
        final_classification = self.determine_final_classification(
            surface_class, funding_check, main_pub
        )
        
        print(f"  ✅ Final classification: {final_classification['classification']}")
        
        return final_classification
    
    def classify_claim_surface(self, title, article_content):
        """Use AI to classify what the claim appears to be on the surface"""
        
        prompt = f"""
Analyze this health claim and classify it by evidence strength.

TITLE: {title}
CONTENT PREVIEW: {article_content[:500] if article_content else 'Not available'}

Classify as ONE of these:
1. ESTABLISHED_FACT - Appears to be overwhelming scientific consensus (e.g., "smoking causes cancer", "water is necessary", "vegetables are healthy")
2. ACTIVE_RESEARCH - Legitimate ongoing scientific debate with quality evidence on multiple sides
3. CONTESTED - Conflicting evidence, unclear which side is correct
4. FRINGE - Lacks credible scientific evidence, likely pseudoscience
5. COMMERCIAL_CLAIM - Primarily promoting a product/service

Return ONLY valid JSON:
{{
    "classification": "ESTABLISHED_FACT",
    "confidence": 8,
    "reasoning": "Brief explanation",
    "key_topics": ["topic1", "topic2"]
}}

Confidence scale 0-10 (10 = absolutely certain of classification)
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You classify health claims objectively based on surface evidence strength, without considering funding sources."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"  ⚠️ Surface classification failed: {e}")
            return {
                "classification": "CONTESTED",
                "confidence": 5,
                "reasoning": "Classification failed, treating as contested",
                "key_topics": []
            }
    
    def funding_reality_check(self, title, main_pub, surface_class):
        """
        Critical check: Does the source have conflicts related to this claim?
        ENHANCED: Avoid false positives for basic health facts
        """
        
        funding = main_pub.get('funding_sources', [])
        conflicts = main_pub.get('conflicts_of_interest', [])
        industry_ties = main_pub.get('industry_ties', [])
        ownership = main_pub.get('ownership', '')
        credibility = main_pub.get('credibility_score', 5.0)
        
        red_flags = []
        
        # Check if this is a basic health fact
        title_lower = title.lower()
        is_basic_fact = any(fact in title_lower for fact in self.basic_health_facts)
        
        # If basic fact AND no product promotion, be lenient
        is_product_promotion = any(word in title_lower for word in [
            'supplement', 'pill', 'cure', 'buy', 'order', 'product'
        ])
        
        if is_basic_fact and not is_product_promotion:
            print(f"  ℹ️ Detected basic health fact - reducing conflict sensitivity")
            # Still check for conflicts, but require stronger evidence
            conflict_threshold = 2  # Need 2+ red flags to trigger
        else:
            conflict_threshold = 1  # Normal threshold
        
        # Check 1: Industry conflict detection
        industry_conflicts = self.detect_industry_conflicts(
            title, 
            surface_class.get('key_topics', []),
            funding, 
            conflicts, 
            industry_ties, 
            ownership,
            is_basic_fact
        )
        
        if industry_conflicts:
            red_flags.extend(industry_conflicts)
        
        # Check 2: Credibility vs claim strength mismatch
        if surface_class['classification'] == 'ESTABLISHED_FACT' and credibility < 6:
            if not is_basic_fact:  # Don't flag for basic facts from moderate sources
                red_flags.append("Low credibility source making authoritative claim")
        
        # Check 3: No primary sources for strong claim
        if surface_class['classification'] == 'ESTABLISHED_FACT':
            if not main_pub.get('primary_source_links') and not is_basic_fact:
                red_flags.append("No links to original research despite strong claim")
        
        # Check 4: Known propaganda patterns
        propaganda_check = self.check_propaganda_patterns(main_pub)
        if propaganda_check:
            red_flags.extend(propaganda_check)
        
        # Check 5: Financial incentive analysis
        financial_incentive = self.analyze_financial_incentive(
            title, 
            surface_class.get('key_topics', []),
            funding, 
            conflicts
        )
        
        if financial_incentive['score'] >= 7:
            red_flags.append(f"Strong financial incentive: {financial_incentive['reason']}")
        
        # Determine status with adjusted threshold
        if len(red_flags) >= conflict_threshold + 2:
            status = "MANUFACTURED_CONSENSUS_SUSPECTED"
        elif len(red_flags) >= conflict_threshold:
            status = "INDUSTRY_NARRATIVE_SUSPECTED"
        else:
            status = "CLEAN"
        
        return {
            'status': status,
            'red_flags': red_flags,
            'conflict_count': len(red_flags),
            'financial_incentive': financial_incentive
        }
    
    def detect_industry_conflicts(self, title, topics, funding, conflicts, industry_ties, ownership, is_basic_fact=False):
        """Check if source has financial ties to industries related to the claim"""
        
        conflicts_found = []
        
        title_lower = title.lower()
        topics_str = ' '.join(topics).lower()
        all_funding = ' '.join([str(f) for f in funding + conflicts + industry_ties + [ownership]]).lower()
        
        # Check each industry pattern
        for industry, keywords in self.conflict_patterns.items():
            # Does the claim involve this industry's products?
            claim_involves_industry = any(
                keyword in title_lower or keyword in topics_str 
                for keyword in keywords
            )
            
            # Does the source have ties to this industry?
            source_tied_to_industry = any(
                industry.replace('_', ' ') in all_funding or
                keyword in all_funding
                for keyword in keywords[:3]
            )
            
            if claim_involves_industry and source_tied_to_industry:
                # For basic facts, only flag if promoting specific products
                if is_basic_fact:
                    promotes_product = any(word in title_lower for word in [
                        'supplement', 'pill', 'product', 'brand', 'buy'
                    ])
                    if promotes_product:
                        conflicts_found.append(
                            f"Basic health fact used to promote {industry.replace('_', ' ')} products"
                        )
                else:
                    conflicts_found.append(
                        f"Claim involves {industry.replace('_', ' ')} products, source has {industry.replace('_', ' ')} funding/ties"
                    )
        
        return conflicts_found
    
    def check_propaganda_patterns(self, main_pub):
        """Check for known propaganda red flags"""
        
        red_flags_in_pub = main_pub.get('red_flags', [])
        patterns = []
        
        propaganda_indicators = [
            'undisclosed', 
            'hidden conflicts', 
            'no source', 
            'no citation',
            'sponsored content',
            'native advertising',
            'paid by'
        ]
        
        for flag in red_flags_in_pub:
            flag_lower = str(flag).lower()
            if any(indicator in flag_lower for indicator in propaganda_indicators):
                patterns.append(f"Propaganda pattern: {flag}")
        
        return patterns
    
    def analyze_financial_incentive(self, title, topics, funding, conflicts):
        """Calculate how much money is at stake"""
        
        title_lower = title.lower()
        topics_str = ' '.join(topics).lower()
        
        high_value_keywords = {
            'pharmaceutical': ['drug', 'medication', 'vaccine', 'treatment', 'prescription'],
            'supplement': ['supplement', 'vitamin', 'pill', 'cure'],
            'medical_device': ['device', 'implant', 'procedure', 'surgery'],
            'weight_loss': ['diet', 'weight loss', 'fat', 'obesity', 'slim']
        }
        
        incentive_score = 0
        reasons = []
        
        for industry, keywords in high_value_keywords.items():
            if any(kw in title_lower or kw in topics_str for kw in keywords):
                incentive_score += 3
                reasons.append(f"{industry.replace('_', ' ')} products mentioned")
        
        funding_str = ' '.join([str(f) for f in funding + conflicts]).lower()
        if any(industry in funding_str for industry in high_value_keywords.keys()):
            incentive_score += 4
            reasons.append("Source funded by industry related to claim")
        
        return {
            'score': min(10, incentive_score),
            'reason': '; '.join(reasons) if reasons else 'No major financial incentive detected'
        }
    
    def determine_final_classification(self, surface_class, funding_check, main_pub):
        """
        Combine surface classification with funding check to get final classification
        """
        
        surface_type = surface_class['classification']
        funding_status = funding_check['status']
        credibility = main_pub.get('credibility_score', 5.0)
        
        if surface_type == "ESTABLISHED_FACT":
            
            if funding_status == "MANUFACTURED_CONSENSUS_SUSPECTED":
                return {
                    'classification': 'MANUFACTURED_CONSENSUS',
                    'confidence': 8,
                    'reasoning': 'Presented as fact but multiple funding conflicts detected',
                    'warning': '⚠️ CRITICAL: Multiple industry conflicts detected despite authoritative claim',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_independently_funded_analysis',
                    'result_label': 'Independent Analysis (No Industry Funding)'
                }
            
            elif funding_status == "INDUSTRY_NARRATIVE_SUSPECTED":
                return {
                    'classification': 'INDUSTRY_NARRATIVE',
                    'confidence': 7,
                    'reasoning': 'Presented as fact but source has industry conflicts',
                    'warning': '⚠️ CAUTION: Industry funding detected for source making authoritative claim',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_independently_funded_analysis',
                    'result_label': 'Independent Analysis (Different Funding)'
                }
            
            elif credibility >= 7:
                return {
                    'classification': 'ESTABLISHED_FACT_VERIFIED',
                    'confidence': surface_class['confidence'],
                    'reasoning': 'Well-established fact from credible independent source',
                    'warning': None,
                    'red_flags': [],
                    'search_strategy': 'search_authoritative_confirmation',
                    'result_label': 'Authoritative Confirmation'
                }
            
            else:
                return {
                    'classification': 'LIKELY_ESTABLISHED',
                    'confidence': 6,
                    'reasoning': 'Appears established but source credibility is moderate',
                    'warning': 'ℹ️ Moderate credibility source',
                    'red_flags': [],
                    'search_strategy': 'search_authoritative_confirmation',
                    'result_label': 'Verification from Higher Credibility Source'
                }
        
        elif surface_type == "COMMERCIAL_CLAIM":
            return {
                'classification': 'COMMERCIAL_CLAIM',
                'confidence': 9,
                'reasoning': 'Primarily promotional content',
                'warning': '🚨 Commercial/promotional content detected',
                'red_flags': ['Commercial content'],
                'search_strategy': 'search_evidence_based_analysis',
                'result_label': 'Evidence-Based Analysis'
            }
        
        elif surface_type == "FRINGE":
            return {
                'classification': 'FRINGE',
                'confidence': surface_class['confidence'],
                'reasoning': surface_class['reasoning'],
                'warning': '🚨 Lacks credible scientific evidence',
                'red_flags': ['Fringe claim'],
                'search_strategy': 'search_debunking',
                'result_label': 'Evidence-Based Analysis'
            }
        
        elif surface_type == "ACTIVE_RESEARCH":
            if funding_status in ["INDUSTRY_NARRATIVE_SUSPECTED", "MANUFACTURED_CONSENSUS_SUSPECTED"]:
                return {
                    'classification': 'CONTESTED_WITH_CONFLICTS',
                    'confidence': 7,
                    'reasoning': 'Active research area but source has conflicts',
                    'warning': '⚠️ Active research area - source has industry ties',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_independently_funded_research',
                    'result_label': 'Independent Research (Different Funding)'
                }
            else:
                return {
                    'classification': 'ACTIVE_RESEARCH',
                    'confidence': surface_class['confidence'],
                    'reasoning': 'Legitimate ongoing scientific inquiry',
                    'warning': 'ℹ️ Active area of research',
                    'red_flags': [],
                    'search_strategy': 'search_recent_peer_reviewed',
                    'result_label': 'Current Research Summary'
                }
        
        else:  # CONTESTED
            if funding_status in ["INDUSTRY_NARRATIVE_SUSPECTED", "MANUFACTURED_CONSENSUS_SUSPECTED"]:
                return {
                    'classification': 'CONTESTED_WITH_CONFLICTS',
                    'confidence': 7,
                    'reasoning': 'Conflicting evidence and industry conflicts',
                    'warning': '⚠️ Conflicting evidence - source has industry ties',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_independently_funded_analysis',
                    'result_label': 'Independent Analysis (No Industry Ties)'
                }
            else:
                return {
                    'classification': 'CONTESTED',
                    'confidence': surface_class['confidence'],
                    'reasoning': 'Conflicting evidence in scientific literature',
                    'warning': 'ℹ️ Contested topic',
                    'red_flags': [],
                    'search_strategy': 'search_multiple_perspectives',
                    'result_label': 'Multiple Perspectives'
                }
