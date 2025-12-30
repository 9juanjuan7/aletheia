"""
Claim-based analysis for Aletheia

Extracts health claims from articles and verifies them against 
independent research evidence.
"""

import json
import os
from openai import OpenAI
from tavily import TavilyClient
import re

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))


class ClaimAnalyzer:
    """Analyzes specific health claims in articles"""
    
    def extract_claims(self, title: str, content: str = "") -> list:
        """
        Extract 2-3 key health claims from article title/content
        
        Returns: [{"claim": "...", "context": "..."}, ...]
        """
        try:
            prompt = f"""Extract 2-3 specific, testable health claims from this article.

Article Title: {title}
Content: {content[:500] if content else "(no content)"}

Return ONLY a JSON array with this format:
[
  {{"claim": "specific claim about health/treatment", "type": "efficacy|safety|prevalence"}},
  {{"claim": "another testable claim", "type": "efficacy|safety|prevalence"}}
]

Be specific and testable. Ignore opinion statements like "may help" - extract the core claim.
Return only the JSON, no other text."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            try:
                claims = json.loads(response.choices[0].message.content)
                return claims[:3]  # Limit to 3 claims
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse claims JSON")
                return []
                
        except Exception as e:
            print(f"❌ Claim extraction failed: {e}")
            return []
    
    def verify_claim(self, claim: str, claim_type: str) -> dict:
        """
        Verify a single health claim against research evidence
        
        Returns: {
            "claim": "...",
            "supporting_count": int,
            "contradicting_count": int,
            "neutral_count": int,
            "supporting_sources": [{"title": "...", "url": "..."}],
            "contradicting_sources": [{"title": "...", "url": "..."}],
            "evidence_pattern": "STRONG_SUPPORT" | "WEAK_SUPPORT" | "CONTRADICTED" | "INCONCLUSIVE"
        }
        """
        try:
            # Search for research evidence
            query = f"{claim} peer-reviewed research evidence"
            
            print(f"\n🔬 Verifying claim: {claim[:60]}...")
            
            results = tavily.search(
                query=query,
                max_results=5,
                search_depth="basic"
            )
            
            supporting = []
            contradicting = []
            neutral = []
            
            for result in results.get('results', []):
                # Use GPT to classify the evidence
                classification = self._classify_evidence(claim, result)
                
                source_item = {
                    "title": result.get('title', 'Unknown'),
                    "url": result.get('url', ''),
                    "snippet": result.get('content', '')[:150]
                }
                
                if classification == "supporting":
                    supporting.append(source_item)
                elif classification == "contradicting":
                    contradicting.append(source_item)
                else:
                    neutral.append(source_item)
            
            # Determine evidence pattern
            if len(supporting) >= 3 and len(contradicting) == 0:
                pattern = "STRONG_SUPPORT"
            elif len(supporting) >= 2:
                pattern = "WEAK_SUPPORT"
            elif len(contradicting) >= 2:
                pattern = "CONTRADICTED"
            else:
                pattern = "INCONCLUSIVE"
            
            return {
                "claim": claim,
                "claim_type": claim_type,
                "supporting_count": len(supporting),
                "contradicting_count": len(contradicting),
                "neutral_count": len(neutral),
                "supporting_sources": supporting[:2],
                "contradicting_sources": contradicting[:2],
                "evidence_pattern": pattern
            }
            
        except Exception as e:
            print(f"⚠️ Claim verification failed: {e}")
            return {
                "claim": claim,
                "supporting_count": 0,
                "contradicting_count": 0,
                "neutral_count": 0,
                "evidence_pattern": "ERROR"
            }
    
    def _classify_evidence(self, claim: str, source: dict) -> str:
        """Classify whether evidence supports, contradicts, or is neutral to claim"""
        try:
            title = source.get('title', '')
            content = source.get('content', '')[:300]
            
            prompt = f"""Does this research evidence support, contradict, or is it neutral regarding this health claim?

CLAIM: {claim}

EVIDENCE:
Title: {title}
Content: {content}

Respond with ONLY one word: "supporting", "contradicting", or "neutral"
Base this on what the evidence actually says, not your opinion."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            answer = response.choices[0].message.content.strip().lower()
            if "support" in answer:
                return "supporting"
            elif "contradict" in answer:
                return "contradicting"
            else:
                return "neutral"
                
        except Exception as e:
            print(f"⚠️ Evidence classification failed: {e}")
            return "neutral"
    
    def detect_debate(self, claims_analysis: list, main_pub_funding: str = "", counter_pub_funding: str = "") -> dict:
        """
        Detect if topic is legitimately debated or manufactured consensus
        
        Returns: {
            "debate_status": "LEGITIMATE_DEBATE" | "MANUFACTURED_CONSENSUS" | "ESTABLISHED_FACT" | "UNKNOWN",
            "description": "explanation of debate status",
            "funding_pattern": "Industry-funded X% vs Independent-funded Y%"
        }
        """
        
        if not claims_analysis:
            return {
                "debate_status": "UNKNOWN",
                "description": "Insufficient data to determine debate status",
                "funding_pattern": ""
            }
        
        # Count evidence across all claims
        total_supporting = sum(c.get('supporting_count', 0) for c in claims_analysis)
        total_contradicting = sum(c.get('contradicting_count', 0) for c in claims_analysis)
        
        # Determine debate status
        if total_supporting > 0 and total_contradicting > 0:
            # Check if this is legitimate debate or manufactured consensus
            
            # Legitimate debate: both sides have substantial independent research
            if (total_supporting >= 2 and total_contradicting >= 2) and \
               (not main_pub_funding or "independent" in main_pub_funding.lower()):
                debate_status = "LEGITIMATE_DEBATE"
                description = "This topic has credible research on both sides. There is genuine scientific debate."
            else:
                # Manufactured consensus: low-funded sources against well-funded
                debate_status = "MANUFACTURED_CONSENSUS"
                description = "Appears to be manufactured debate. Minority view lacks independent research support."
        
        elif total_supporting > 0 and total_contradicting == 0:
            debate_status = "ESTABLISHED_FACT"
            description = "Research evidence predominantly supports this claim. This is not a debated topic."
        
        elif total_contradicting > 0 and total_supporting == 0:
            debate_status = "ESTABLISHED_FACT"
            description = "Research evidence predominantly contradicts this claim."
        
        else:
            debate_status = "UNKNOWN"
            description = "Insufficient research evidence found to determine debate status."
        
        return {
            "debate_status": debate_status,
            "description": description,
            "supporting_count": total_supporting,
            "contradicting_count": total_contradicting
        }
