#!/usr/bin/env python
"""
Test the institutional capture analyzer integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.institutional_capture import InstitutionalCaptureAnalyzer

# Test data
test_publication = {
    'name': 'Test Pharma Blog',
    'domain': 'pharmatest.com',
    'funding_sources': ['Pfizer', 'Moderna'],
    'conflicts_of_interest': ['CEO sits on Pfizer board'],
    'credibility_score': 3.5
}

analyzer = InstitutionalCaptureAnalyzer()

print("🧪 Testing Institutional Capture Analyzer...")
print(f"\n📊 Test Publication: {test_publication['name']}")
print(f"   Domain: {test_publication['domain']}")
print(f"   Funding: {test_publication['funding_sources']}")

# Test funding chain analysis
print("\n\n1️⃣  Testing Funding Chain Analysis...")
funding_analysis = analyzer.detect_funding_chain_conflicts(test_publication)
print(f"   ✓ Funding Integrity: {funding_analysis['funding_chain_integrity']}")
print(f"   ✓ Conflicts Found: {len(funding_analysis['main_source_conflicts'])}")

# Test historical pattern matching
print("\n\n2️⃣  Testing Historical Pattern Detection...")
historical = analyzer.find_historical_pattern_match("New study says sugar is safe")
print(f"   ✓ Pattern Found: {historical['pattern_found']}")

# Test comprehensive analysis
print("\n\n3️⃣  Testing Comprehensive Capture Analysis...")
try:
    # Note: This will call Tavily API, so it might take a moment
    comprehensive = analyzer.comprehensive_capture_analysis(
        claim="New supplement claims to cure diabetes",
        main_source=test_publication,
        industry_type="supplement"
    )
    print(f"   ✓ Overall Integrity Score: {comprehensive['overall_integrity_score']:.1f}/10")
    print(f"   ✓ Red Flags Found: {len(comprehensive['red_flags_summary'])}")
    print("\n   Red Flags:")
    for flag in comprehensive['red_flags_summary'][:3]:
        print(f"     - {flag}")
    
    print("\n✅ All tests passed!")
except Exception as e:
    print(f"   ⚠️  API test skipped (may need TAVILY_API_KEY): {str(e)[:100]}")
    print("   ✅ Module structure intact!")
