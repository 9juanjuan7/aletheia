#!/usr/bin/env python
"""Test the analyze functionality directly without Flask"""

import json
from services.claim_analyzer import ClaimAnalyzer

def test_kiwi_claim():
    print("=" * 60)
    print("TESTING: Kiwi article classification")
    print("=" * 60)
    
    analyzer = ClaimAnalyzer()
    
    # Mock publication data for USA Today
    mock_pub = {
        "name": "USA Today",
        "domain": "usatoday.com",
        "credibility_score": 4.0,
        "funding_sources": ["Advertising", "Gannett Media"],
        "conflicts_of_interest": [],
        "industry_ties": [],
        "ownership": "Gannett",
        "red_flags": [],
        "green_flags": ["Major news organization"]
    }
    
    title = "Are kiwis good for you? What dietitians say"
    article_content = "Kiwis are packed with vitamin C and other nutrients..."
    
    result = analyzer.analyze_claim(title, article_content, mock_pub)
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print(json.dumps(result, indent=2))
    print("=" * 60)
    
    # Check if it's NOT manufactured consensus
    classification = result.get('classification', '')
    if classification == 'MANUFACTURED_CONSENSUS':
        print("\n❌ FAIL: Still classifying as MANUFACTURED_CONSENSUS!")
    elif classification in ['ESTABLISHED_FACT', 'ESTABLISHED_FACT_VERIFIED', 'ESTABLISHED_FACT_IMPERFECT_SOURCE', 'LIKELY_ESTABLISHED']:
        print(f"\n✅ PASS: Correctly classified as {classification}")
    else:
        print(f"\n⚠️ UNEXPECTED: Classification is {classification}")

if __name__ == "__main__":
    test_kiwi_claim()
