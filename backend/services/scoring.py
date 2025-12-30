"""
Multi-dimensional credibility scoring for Aletheia

Separates funding independence, claim accuracy, and source quality.
"""

def calculate_funding_independence_score(publication: dict) -> float:
    """
    Score how independent a publication is from commercial interests
    
    Ranges: 0-10
    - 0-2: Heavy industry/pharma funding with conflicts
    - 3-4: Mixed funding with corporate ties
    - 5-6: Balanced but has some conflicts
    - 7-8: Mostly independent with some advertising
    - 9-10: Fully independent, nonprofit, or government
    """
    
    score = 5.0  # Start neutral
    
    funding_sources = publication.get('funding_sources', [])
    conflicts = publication.get('conflicts_of_interest', [])
    
    # Penalties for obvious conflicts
    for conflict in conflicts:
        conflict_lower = conflict.lower()
        
        if any(x in conflict_lower for x in ['pharma', 'drug', 'manufacturer', 'company']):
            score -= 2.5
        elif any(x in conflict_lower for x in ['advertising', 'sponsored']):
            score -= 1.5
        elif any(x in conflict_lower for x in ['invested', 'owns', 'subsidiary']):
            score -= 2.0
    
    # Bonuses for transparency
    transparency = publication.get('funding_transparency', 'unknown').lower()
    if transparency == 'high':
        score += 1.5
    elif transparency == 'low':
        score -= 1.5
    
    # Check funding sources
    if funding_sources:
        independent_sources = sum(1 for f in funding_sources 
                                 if any(x in f.lower() for x in ['nonprofit', 'grant', 'government', 'independent', 'foundation']))
        commercial_sources = sum(1 for f in funding_sources 
                                if any(x in f.lower() for x in ['pharma', 'drug', 'advertising', 'marketing']))
        
        if independent_sources > commercial_sources:
            score += 1.0
        elif commercial_sources > independent_sources:
            score -= 1.5
    
    return max(0, min(10, score))


def analyze_research_support_pattern(claims_analysis: list) -> dict:
    """
    Analyze the pattern of research support for claims
    
    Returns a classification label instead of a score:
    - "Established Consensus": 80%+ of sources agree, multiple independent studies
    - "Mixed Evidence": Some sources support, some contradict, legitimate debate
    - "Limited Research": Only a few studies exist, preliminary findings
    - "Evidence Gaps": Claim is too specific/vague to verify against research
    - "Contradicted by Research": Majority of sources contradict the claim
    """
    
    if not claims_analysis:
        return {
            'pattern': 'Evidence Gaps',
            'description': 'No claims were analyzed to compare against research.'
        }
    
    total_supporting = sum(c.get('supporting_count', 0) for c in claims_analysis)
    total_contradicting = sum(c.get('contradicting_count', 0) for c in claims_analysis)
    total_evidence = total_supporting + total_contradicting
    
    if total_evidence == 0:
        return {
            'pattern': 'Evidence Gaps',
            'description': 'Limited research available to verify these specific claims.'
        }
    
    support_ratio = total_supporting / total_evidence
    
    # Classify based on ratio and volume
    if support_ratio >= 0.8 and total_evidence >= 4:
        return {
            'pattern': 'Established Consensus',
            'description': f'Majority of research ({total_supporting} supporting sources) aligns with these claims.'
        }
    elif support_ratio >= 0.3 and support_ratio <= 0.7 and total_evidence >= 2:
        return {
            'pattern': 'Mixed Evidence',
            'description': f'Research shows conflicting results ({total_supporting} supporting, {total_contradicting} contradicting). This is a legitimate area of scientific debate.'
        }
    elif total_evidence <= 2:
        return {
            'pattern': 'Limited Research',
            'description': f'Only {total_evidence} research source(s) found. These are preliminary or emerging findings.'
        }
    elif support_ratio < 0.3:
        return {
            'pattern': 'Contradicted by Research',
            'description': f'Most research ({total_contradicting} sources) contradicts or does not support these claims.'
        }
    else:
        return {
            'pattern': 'Evidence Gaps',
            'description': 'Insufficient research available for reliable verification.'
        }


def calculate_claim_accuracy_score(claims_analysis: list) -> float:
    """
    DEPRECATED: Use analyze_research_support_pattern instead.
    
    Kept for backwards compatibility only.
    Returns a score based on research support pattern.
    """
    
    if not claims_analysis:
        return 5.0
    
    total_supporting = sum(c.get('supporting_count', 0) for c in claims_analysis)
    total_contradicting = sum(c.get('contradicting_count', 0) for c in claims_analysis)
    
    total_evidence = total_supporting + total_contradicting
    
    if total_evidence == 0:
        return 5.0
    
    support_ratio = total_supporting / total_evidence if total_evidence > 0 else 0.5
    
    if support_ratio >= 0.9:
        score = 9.0
    elif support_ratio >= 0.7:
        score = 7.5
    elif support_ratio >= 0.5:
        score = 5.5
    elif support_ratio >= 0.3:
        score = 3.5
    else:
        score = 2.0
    
    if total_evidence < 2:
        score *= 0.7
    elif total_evidence >= 4:
        score = min(10, score + 0.5)
    
    return max(0, min(10, score))


def calculate_source_quality_score(publication: dict) -> float:
    """
    Score how credible the source is based on citation practices
    
    Ranges: 0-10
    - 0-2: No citations, all promotional language
    - 3-4: Some citations but mostly indirect or missing
    - 5-6: Decent citations but lacks primary sources
    - 7-8: Good citations with primary sources
    - 9-10: Excellent peer-reviewed or primary source citations
    """
    
    score = 5.0  # Start neutral
    
    green_flags = publication.get('green_flags', [])
    red_flags = publication.get('red_flags', [])
    
    # Check green flags (citations, methodology, etc)
    for flag in green_flags:
        flag_lower = flag.lower()
        if any(x in flag_lower for x in ['peer-reviewed', 'peer reviewed', 'citation', 'study']):
            score += 1.5
        elif any(x in flag_lower for x in ['primary source', 'published', 'methodology']):
            score += 1.0
        elif any(x in flag_lower for x in ['credential', 'expert', 'qualified']):
            score += 0.5
    
    # Check red flags (missing citations, promotional)
    for flag in red_flags:
        flag_lower = flag.lower()
        if any(x in flag_lower for x in ['no citation', 'missing', 'unverified']):
            score -= 1.5
        elif any(x in flag_lower for x in ['promotional', 'marketing', 'sponsored']):
            score -= 1.0
        elif any(x in flag_lower for x in ['unsubstantiated', 'claim']):
            score -= 0.5
    
    # Check domain reputation
    domain = publication.get('domain', '').lower()
    
    if any(x in domain for x in ['pubmed', 'ncbi', 'nature.com', 'science.org', 'thelancet', 'jama']):
        score += 2.0  # Major journal
    elif '.edu' in domain:
        score += 1.0  # Academic
    elif '.gov' in domain:
        score += 1.5  # Government
    elif any(x in domain for x in ['wordpress', 'medium', 'substack', 'blogger']):
        score -= 2.0  # Blog platform
    
    return max(0, min(10, score))


def calculate_nuanced_recommendation(funding_score: float, accuracy_score: float, 
                                   quality_score: float, debate_status: str) -> str:
    """
    Generate a neutral, nuanced recommendation
    """
    
    if debate_status == "LEGITIMATE_DEBATE":
        return "This topic has credible research supporting different viewpoints. Review both sides of the debate."
    
    elif debate_status == "MANUFACTURED_CONSENSUS":
        return "The majority research contradicts this claim. The contrarian view lacks independent research support."
    
    elif debate_status == "ESTABLISHED_FACT":
        if accuracy_score >= 7.0:
            return "This claim has strong independent research support."
        else:
            return "This claim is contradicted by research evidence."
    
    # General nuanced recommendations
    if funding_score < 3.0:
        if accuracy_score >= 7.0:
            return "The source has funding conflicts, BUT the specific claims have strong independent verification. Verify funding bias doesn't undermine methodology."
        else:
            return "Funding conflicts detected AND claims lack research support. Approach with caution."
    
    elif quality_score < 4.0:
        if accuracy_score >= 7.0:
            return "Poor citation practices, but specific claims are well-supported by independent research. Seek original sources."
        else:
            return "Poor citation practices AND weak claim verification. Look for better sources."
    
    else:
        # Generally good
        if accuracy_score >= 7.0:
            return "Claims are well-supported by research. Publication has reasonable credibility."
        elif accuracy_score >= 5.0:
            return "Mixed evidence for claims. Publication quality is adequate but evidence is inconclusive."
        else:
            return "Research evidence contradicts the claims in this article."
