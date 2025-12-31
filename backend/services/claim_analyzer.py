import os
from dotenv import load_dotenv
from groq import Groq
import json
from datetime import datetime

load_dotenv()

# Lazy-loaded client
_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return _groq_client

class ClaimAnalyzer:
    """
    Multi-dimensional claim classification system
    
    Key Philosophy: Funding bias matters most when claims are CONTESTED.
    Well-established claims with independent corroboration should NOT be
    flagged as "manufactured consensus" just because reporting source has ads.
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
        
        # Basic uncontroversial health facts - these require strong evidence to flag
        # Include common healthy foods so "kiwis are good" isn't flagged
        self.basic_health_facts = [
            'vegetables', 'fruits', 'water', 'hydration', 'exercise', 'sleep',
            'hygiene', 'handwashing', 'smoking harmful', 'physical activity',
            'fiber', 'whole grains', 'vitamin c', 'antioxidants', 'nutrients',
            # Common fruits - established as healthy
            'apple', 'banana', 'orange', 'kiwi', 'berry', 'berries', 'grape',
            'strawberry', 'blueberry', 'mango', 'watermelon', 'peach', 'pear',
            'avocado', 'cherry', 'lemon', 'lime', 'grapefruit', 'pineapple',
            # Common vegetables
            'broccoli', 'spinach', 'kale', 'carrot', 'tomato', 'cucumber',
            'lettuce', 'pepper', 'onion', 'garlic', 'potato', 'sweet potato',
            'cauliflower', 'asparagus', 'celery', 'zucchini', 'mushroom',
            # Other healthy foods
            'nuts', 'almonds', 'walnuts', 'fish', 'salmon', 'olive oil',
            'beans', 'lentils', 'legumes', 'quinoa', 'oats', 'eggs',
            # General health terms
            'diet', 'nutrition', 'healthy eating', 'balanced diet'
        ]
        
        # Claims that are scientifically well-established
        self.established_claim_patterns = [
            'contain', 'has', 'includes', 'source of', 'provides', 'rich in',
            'good for', 'healthy', 'nutritious', 'beneficial'
        ]
        
        # Causal claims that require stronger evidence
        self.causal_claim_patterns = [
            'prevents', 'causes', 'cures', 'treats', 'reduces risk',
            'leads to', 'results in', 'protects against', 'fights',
            'eliminates', 'reverses', 'heals'
        ]
        
        # Product promotion indicators
        self.product_promotion_indicators = [
            'supplement', 'pill', 'buy', 'order', 'product', 'brand',
            'our', 'try', 'discount', 'sale', 'exclusive', 'best'
        ]
    
    def analyze_claim(self, title, article_content, main_pub):
        """
        Multi-layer analysis:
        1. Classify claim complexity (basic fact vs causal claim)
        2. Surface classification (what it appears to be)
        3. Check if claim is independently established
        4. Funding reality check (only heavily weighted for contested claims)
        """
        
        print(f"\n🔍 CLAIM ANALYSIS: {title[:60]}...")
        
        # Layer 0: Claim complexity assessment
        claim_complexity = self.classify_claim_complexity(title)
        print(f"  📊 Claim complexity: {claim_complexity['type']} (funding_sensitivity: {claim_complexity['funding_sensitivity']})")
        
        # Layer 1: Surface classification
        surface_class = self.classify_claim_surface(title, article_content)
        print(f"  📋 Surface classification: {surface_class['classification']}")
        
        # Layer 2: Check if claim is independently established
        establishment_status = self.assess_claim_establishment(
            title, surface_class, claim_complexity
        )
        print(f"  🔬 Establishment status: {establishment_status['status']} (requires_scrutiny: {establishment_status['requires_funding_scrutiny']})")
        
        # Layer 3: Funding reality check (weight depends on establishment)
        funding_check = self.funding_reality_check(
            title, main_pub, surface_class, establishment_status, claim_complexity
        )
        print(f"  💰 Funding check: {funding_check['status']} (flags: {len(funding_check.get('red_flags', []))})")
        
        # Final classification
        final_classification = self.determine_final_classification(
            surface_class, funding_check, main_pub, establishment_status, claim_complexity
        )
        
        print(f"  ✅ Final classification: {final_classification['classification']}")
        
        return final_classification
    
    def classify_claim_complexity(self, title):
        """
        Distinguish between claim types - basic facts require less scrutiny.
        
        Returns: {
            "type": "BASIC_FACT" | "CAUSAL_CLAIM" | "COMPLEX_CLAIM",
            "requires_strong_evidence": bool,
            "funding_sensitivity": "LOW" | "MEDIUM" | "HIGH"
        }
        """
        title_lower = title.lower()
        
        # Check for causal claims (require strongest evidence)
        has_causal = any(pattern in title_lower for pattern in self.causal_claim_patterns)
        
        # Check for basic factual claims
        has_basic = any(pattern in title_lower for pattern in self.established_claim_patterns)
        
        # Check for product promotion
        has_product = any(pattern in title_lower for pattern in self.product_promotion_indicators)
        
        # Check for basic health topics
        is_basic_topic = any(fact in title_lower for fact in self.basic_health_facts)
        
        if has_product:
            return {
                "type": "COMMERCIAL_CLAIM",
                "requires_strong_evidence": True,
                "funding_sensitivity": "HIGH"
            }
        elif has_causal:
            return {
                "type": "CAUSAL_CLAIM",
                "requires_strong_evidence": True,
                "funding_sensitivity": "HIGH"
            }
        elif has_basic and is_basic_topic:
            return {
                "type": "BASIC_FACT",
                "requires_strong_evidence": False,
                "funding_sensitivity": "LOW"
            }
        elif has_basic:
            return {
                "type": "SIMPLE_CLAIM",
                "requires_strong_evidence": False,
                "funding_sensitivity": "MEDIUM"
            }
        else:
            return {
                "type": "COMPLEX_CLAIM",
                "requires_strong_evidence": True,
                "funding_sensitivity": "MEDIUM"
            }
    
    def assess_claim_establishment(self, title, surface_class, claim_complexity):
        """
        Determine if claim is well-established independent of source funding.
        
        Key insight: "Kiwis have vitamin C" is established regardless of who says it.
        "Breakfast is the most important meal" is NOT established - it's contested.
        
        Returns: {
            "status": "ESTABLISHED" | "CONTESTED" | "NOVEL",
            "independent_support_likely": bool,
            "requires_funding_scrutiny": bool
        }
        """
        
        title_lower = title.lower()
        surface_type = surface_class.get('classification', 'CONTESTED')
        complexity_type = claim_complexity.get('type', 'COMPLEX_CLAIM')
        
        # Basic facts about nutrition/health are generally established
        if complexity_type == "BASIC_FACT":
            # "Fruits are healthy", "Exercise is good" - established facts
            return {
                "status": "ESTABLISHED",
                "independent_support_likely": True,
                "requires_funding_scrutiny": False
            }
        
        # Contested topic indicators - these require more scrutiny
        contested_indicators = [
            'breakfast', 'most important meal',  # Cereal industry pushed
            'moderate alcohol', 'red wine benefits',  # Alcohol industry pushed
            'natural sugar', 'fruit sugar',  # Sugar industry pushed
            'low fat', 'fat free',  # Historical food industry push
            'detox', 'cleanse',  # Pseudoscience
            'superfood',  # Marketing term
        ]
        
        is_likely_contested = any(ind in title_lower for ind in contested_indicators)
        
        if is_likely_contested:
            return {
                "status": "CONTESTED",
                "independent_support_likely": False,
                "requires_funding_scrutiny": True
            }
        
        # If AI classified as ESTABLISHED_FACT and no contested indicators
        if surface_type == "ESTABLISHED_FACT" and not is_likely_contested:
            if complexity_type in ["BASIC_FACT", "SIMPLE_CLAIM"]:
                return {
                    "status": "ESTABLISHED",
                    "independent_support_likely": True,
                    "requires_funding_scrutiny": False
                }
        
        # Commercial claims always need scrutiny
        if complexity_type == "COMMERCIAL_CLAIM":
            return {
                "status": "NOVEL",
                "independent_support_likely": False,
                "requires_funding_scrutiny": True
            }
        
        # Causal claims need verification
        if complexity_type == "CAUSAL_CLAIM":
            return {
                "status": "CONTESTED",
                "independent_support_likely": False,
                "requires_funding_scrutiny": True
            }
        
        # Default: treat as needing verification
        return {
            "status": "CONTESTED",
            "independent_support_likely": False,
            "requires_funding_scrutiny": True
        }
    
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
            response = get_groq_client().chat.completions.create(
                model="llama-3.3-70b-versatile",
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
    
    def funding_reality_check(self, title, main_pub, surface_class, establishment_status, claim_complexity):
        """
        Critical check: Does the source have conflicts related to this claim?
        
        KEY PHILOSOPHY: Funding matters most for CONTESTED claims.
        For ESTABLISHED claims, funding bias is informational but not disqualifying.
        """
        
        funding = main_pub.get('funding_sources', [])
        conflicts = main_pub.get('conflicts_of_interest', [])
        industry_ties = main_pub.get('industry_ties', [])
        ownership = main_pub.get('ownership', '')
        credibility = main_pub.get('credibility_score', 5.0)
        
        red_flags = []
        
        # Get establishment and complexity info
        claim_established = establishment_status.get('status') == 'ESTABLISHED'
        requires_scrutiny = establishment_status.get('requires_funding_scrutiny', True)
        funding_sensitivity = claim_complexity.get('funding_sensitivity', 'MEDIUM')
        claim_type = claim_complexity.get('type', 'COMPLEX_CLAIM')
        
        title_lower = title.lower()
        
        # For established claims with low funding sensitivity, be very lenient
        if claim_established and funding_sensitivity == 'LOW':
            # Only flag for egregious cases (direct product promotion)
            is_product_promotion = any(word in title_lower for word in self.product_promotion_indicators)
            
            if is_product_promotion:
                red_flags.append("Product promotion detected even for established claim")
                return {
                    'status': "INDUSTRY_NARRATIVE_SUSPECTED",
                    'red_flags': red_flags,
                    'conflict_count': 1,
                    'financial_incentive': {'score': 5, 'reason': 'Product promotion'}
                }
            else:
                # Established fact, no product promotion - CLEAN
                return {
                    'status': "CLEAN",
                    'red_flags': [],
                    'conflict_count': 0,
                    'financial_incentive': {'score': 0, 'reason': 'Established fact, no product promotion'}
                }
        
        # For contested claims or high funding sensitivity, apply full scrutiny
        if requires_scrutiny or funding_sensitivity == 'HIGH':
            
            # Check 1: Industry conflict detection (but smarter)
            industry_conflicts = self.detect_industry_conflicts_smart(
                title, 
                surface_class.get('key_topics', []),
                funding, 
                conflicts, 
                industry_ties, 
                ownership,
                claim_type,
                claim_established
            )
            
            if industry_conflicts:
                red_flags.extend(industry_conflicts)
            
            # Check 2: Credibility vs claim strength mismatch
            if surface_class['classification'] == 'ESTABLISHED_FACT' and credibility < 5:
                red_flags.append("Low credibility source making authoritative claim")
            
            # Check 3: No primary sources for contested claim
            if not claim_established:
                if not main_pub.get('primary_source_links'):
                    red_flags.append("No primary source links for contested claim")
            
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
            
            # Only add financial incentive red flag for contested claims
            if financial_incentive['score'] >= 7 and not claim_established:
                red_flags.append(f"Strong financial incentive: {financial_incentive['reason']}")
        
        else:
            # Moderate scrutiny for MEDIUM sensitivity established claims
            financial_incentive = {'score': 0, 'reason': 'Low risk claim type'}
        
        # Determine status based on red flags AND establishment status
        if claim_established:
            # For established claims, require MORE red flags to trigger warnings
            if len(red_flags) >= 3:
                status = "FUNDING_BIAS_DETECTED"  # New status - bias but claim is still valid
            else:
                status = "CLEAN"
        else:
            # For contested claims, apply normal thresholds
            if len(red_flags) >= 2:
                status = "MANUFACTURED_CONSENSUS_SUSPECTED"
            elif len(red_flags) >= 1:
                status = "INDUSTRY_NARRATIVE_SUSPECTED"
            else:
                status = "CLEAN"
        
        return {
            'status': status,
            'red_flags': red_flags,
            'conflict_count': len(red_flags),
            'financial_incentive': financial_incentive if requires_scrutiny else {'score': 0, 'reason': 'Low risk'}
        }
    
    def detect_industry_conflicts_smart(self, title, topics, funding, conflicts, industry_ties, ownership, claim_type, claim_established):
        """
        Smart industry conflict detection.
        
        KEY INSIGHT: Just because a food site talks about food doesn't mean conflict.
        True conflict = financial incentive TO PUSH A SPECIFIC POSITION on a contested claim.
        """
        
        conflicts_found = []
        
        title_lower = title.lower()
        topics_str = ' '.join(topics).lower()
        all_funding = ' '.join([str(f) for f in funding + conflicts + industry_ties + [ownership]]).lower()
        
        # For BASIC_FACT claims, only flag if promoting specific products
        if claim_type == "BASIC_FACT":
            if any(word in title_lower for word in self.product_promotion_indicators):
                conflicts_found.append("Product promotion detected in basic fact article")
            # Otherwise, no conflict for basic facts
            return conflicts_found
        
        # For established claims, only flag DIRECT ownership conflicts
        if claim_established:
            # Check for direct ownership by industry
            direct_ownership_keywords = ['owned by', 'subsidiary of', 'pharmaceutical company', 'drug company']
            if any(kw in all_funding for kw in direct_ownership_keywords):
                conflicts_found.append("Source directly owned by industry with stake in claim")
            return conflicts_found
        
        # For contested/causal claims, apply normal conflict detection
        # But be smarter - require SPECIFIC industry match, not just topic overlap
        
        high_risk_claim_patterns = {
            'pharmaceutical': ['drug', 'medication', 'prescription', 'treatment'],
            'supplement': ['supplement', 'pill', 'cure', 'remedy'],
            'alcohol': ['alcohol', 'wine', 'beer', 'moderate drinking'],
            'tobacco': ['smoking', 'vaping', 'nicotine'],
        }
        
        for industry, keywords in high_risk_claim_patterns.items():
            claim_about_industry = any(kw in title_lower for kw in keywords)
            source_funded_by_industry = industry in all_funding or any(kw in all_funding for kw in keywords)
            
            if claim_about_industry and source_funded_by_industry:
                conflicts_found.append(
                    f"Claim about {industry} products from {industry}-funded source"
                )
        
        # Generic food/nutrition articles from ad-supported sites are NOT automatic conflicts
        # Only flag if there's a specific product being pushed
        if 'food' in title_lower or 'nutrition' in title_lower:
            if any(word in title_lower for word in ['brand', 'product', 'buy', 'our']):
                conflicts_found.append("Food article with product placement")
        
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
    
    def determine_final_classification(self, surface_class, funding_check, main_pub, establishment_status, claim_complexity):
        """
        Combine all layers to get final classification.
        
        KEY PHILOSOPHY:
        - ESTABLISHED claims with funding bias = "ESTABLISHED_FACT_IMPERFECT_SOURCE" (not manufactured)
        - CONTESTED claims with funding bias = "MANUFACTURED_CONSENSUS_SUSPECTED"
        - ESTABLISHED claims with no bias = "ESTABLISHED_FACT_VERIFIED"
        """
        
        surface_type = surface_class['classification']
        funding_status = funding_check['status']
        credibility = main_pub.get('credibility_score', 5.0)
        claim_established = establishment_status.get('status') == 'ESTABLISHED'
        claim_complexity_type = claim_complexity.get('type', 'COMPLEX_CLAIM')
        
        # === ESTABLISHED CLAIMS ===
        if claim_established or surface_type == "ESTABLISHED_FACT":
            
            if funding_status == "CLEAN":
                # Perfect case - established fact from clean source
                if credibility >= 7:
                    return {
                        'classification': 'ESTABLISHED_FACT_VERIFIED',
                        'confidence': 9,
                        'reasoning': 'Well-established fact from credible independent source',
                        'warning': None,
                        'red_flags': [],
                        'search_strategy': 'search_authoritative_confirmation',
                        'result_label': 'Authoritative Confirmation'
                    }
                else:
                    return {
                        'classification': 'ESTABLISHED_FACT',
                        'confidence': 7,
                        'reasoning': 'Established fact from moderate credibility source',
                        'warning': None,
                        'red_flags': [],
                        'search_strategy': 'search_authoritative_confirmation',
                        'result_label': 'Verification Source'
                    }
            
            elif funding_status == "FUNDING_BIAS_DETECTED":
                # KEY NEW CATEGORY: Established fact but source has bias
                # Don't flag as manufactured - the claim is still valid
                return {
                    'classification': 'ESTABLISHED_FACT_IMPERFECT_SOURCE',
                    'confidence': 7,
                    'reasoning': 'Claim is well-established but source has funding bias. Claim validity not affected.',
                    'warning': 'ℹ️ Source has funding interests, but claim is independently verified',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_authoritative_confirmation',
                    'result_label': 'Independent Confirmation'
                }
            
            elif funding_status in ["MANUFACTURED_CONSENSUS_SUSPECTED", "INDUSTRY_NARRATIVE_SUSPECTED"]:
                # Even with heavy bias, if claim is established, don't call it manufactured
                if claim_established and claim_complexity_type in ["BASIC_FACT", "SIMPLE_CLAIM"]:
                    return {
                        'classification': 'ESTABLISHED_FACT_IMPERFECT_SOURCE',
                        'confidence': 6,
                        'reasoning': 'Source has significant funding conflicts but claim type suggests independent verifiability',
                        'warning': '⚠️ Source has notable funding conflicts - verify with independent source',
                        'red_flags': funding_check['red_flags'],
                        'search_strategy': 'search_authoritative_confirmation',
                        'result_label': 'Independent Verification'
                    }
                else:
                    # More complex claim with conflicts - treat with more scrutiny
                    return {
                        'classification': 'NEEDS_VERIFICATION',
                        'confidence': 5,
                        'reasoning': 'Claim presented as established but source conflicts warrant verification',
                        'warning': '⚠️ Verify this claim with independent sources',
                        'red_flags': funding_check['red_flags'],
                        'search_strategy': 'search_independently_funded_analysis',
                        'result_label': 'Independent Analysis'
                    }
            
            else:
                return {
                    'classification': 'LIKELY_ESTABLISHED',
                    'confidence': 6,
                    'reasoning': 'Appears established but verification recommended',
                    'warning': None,
                    'red_flags': [],
                    'search_strategy': 'search_authoritative_confirmation',
                    'result_label': 'Verification from Higher Credibility Source'
                }
        
        # === COMMERCIAL CLAIMS ===
        elif surface_type == "COMMERCIAL_CLAIM" or claim_complexity_type == "COMMERCIAL_CLAIM":
            return {
                'classification': 'COMMERCIAL_CLAIM',
                'confidence': 9,
                'reasoning': 'Primarily promotional content',
                'warning': '🚨 Commercial/promotional content detected',
                'red_flags': ['Commercial content'],
                'search_strategy': 'search_evidence_based_analysis',
                'result_label': 'Evidence-Based Analysis'
            }
        
        # === FRINGE CLAIMS ===
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
        
        # === CONTESTED CLAIMS (funding matters most here) ===
        elif surface_type in ["CONTESTED", "ACTIVE_RESEARCH"] or establishment_status.get('status') == 'CONTESTED':
            
            if funding_status == "MANUFACTURED_CONSENSUS_SUSPECTED":
                # THIS is the real manufactured consensus case
                return {
                    'classification': 'MANUFACTURED_CONSENSUS',
                    'confidence': 8,
                    'reasoning': 'Contested claim with strong industry funding pattern favoring this position',
                    'warning': '🚨 CRITICAL: Disputed claim with significant industry funding. Independent research may show conflicting findings.',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_independently_funded_analysis',
                    'result_label': 'Independent Analysis (No Industry Funding)'
                }
            
            elif funding_status == "INDUSTRY_NARRATIVE_SUSPECTED":
                return {
                    'classification': 'INDUSTRY_NARRATIVE',
                    'confidence': 7,
                    'reasoning': 'Contested claim from source with industry conflicts',
                    'warning': '⚠️ CAUTION: Disputed topic - source has industry funding',
                    'red_flags': funding_check['red_flags'],
                    'search_strategy': 'search_independently_funded_analysis',
                    'result_label': 'Independent Analysis (Different Funding)'
                }
            
            else:
                # Contested but no conflicts
                return {
                    'classification': 'LEGITIMATE_DEBATE',
                    'confidence': surface_class['confidence'],
                    'reasoning': 'Legitimate ongoing scientific debate',
                    'warning': 'ℹ️ Active area of research with differing viewpoints',
                    'red_flags': [],
                    'search_strategy': 'search_multiple_perspectives',
                    'result_label': 'Multiple Perspectives'
                }
        
        # === NOVEL CLAIMS ===
        elif establishment_status.get('status') == 'NOVEL':
            return {
                'classification': 'INSUFFICIENT_EVIDENCE',
                'confidence': 4,
                'reasoning': 'Novel claim without sufficient independent verification',
                'warning': '⚠️ Insufficient evidence to verify claim',
                'red_flags': funding_check.get('red_flags', []),
                'search_strategy': 'search_evidence_based_analysis',
                'result_label': 'Evidence Analysis'
            }
        
        # === DEFAULT ===
        else:
            return {
                'classification': 'CONTESTED',
                'confidence': 5,
                'reasoning': 'Unable to fully classify - treating as contested',
                'warning': 'ℹ️ Verify with additional sources',
                'red_flags': [],
                'search_strategy': 'search_multiple_perspectives',
                'result_label': 'Multiple Perspectives'
            }

