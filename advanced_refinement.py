#!/usr/bin/env python3
"""
Advanced Example: Iterative Search Refinement with AI

This script demonstrates how to use Claude to iteratively refine
your search until you find the optimal target audience.

Use Case: Find CEOs in Colorado, but intelligently narrow down
to the most relevant audience based on company characteristics.
"""

import requests
import json
from anthropic import Anthropic


# ============================================================================
# Configuration
# ============================================================================
INSTANTLY_API_KEY = "your_instantly_api_key_here"
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"

BASE_URL = "https://api.instantly.ai/api/v2"
MAX_ITERATIONS = 5


# ============================================================================
# Helper Functions
# ============================================================================

def preview_search(filters: dict) -> dict:
    """Preview search results without spending credits"""
    response = requests.post(
        f"{BASE_URL}/supersearch-enrichment/preview-leads-from-supersearch",
        headers={
            "Authorization": f"Bearer {INSTANTLY_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"search_filters": filters}
    )
    response.raise_for_status()
    return response.json()


def get_ai_refinement_suggestions(
    filters: dict,
    count: int,
    goal: str,
    iteration: int,
    previous_counts: list
) -> dict:
    """Get AI suggestions for refining the search"""
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    history = "\n".join([
        f"Iteration {i+1}: {c:,} leads"
        for i, c in enumerate(previous_counts)
    ])
    
    prompt = f"""You're helping refine a lead search in Instantly.ai SuperSearch.

GOAL: {goal}

TARGET RANGE: 500-2,000 leads (optimal for manageable enrichment)

CURRENT STATUS:
• Iteration: {iteration}
• Current Count: {count:,} leads
• Previous Counts:
{history}

CURRENT FILTERS:
{json.dumps(filters, indent=2)}

AVAILABLE ADJUSTMENTS:
1. Company size (min/max employees)
2. Industries (add/remove)
3. Job titles (add/remove/exclude)
4. Revenue range
5. Technologies used
6. Keywords (hiring, funded, growing, etc.)
7. Funding stage
8. Geographic specificity (add cities, exclude areas)

ANALYSIS NEEDED:
1. Is {count:,} leads in the optimal range (500-2,000)?
2. If not, what's the most impactful filter adjustment?
3. Are we converging on the right target or should we pivot?

Respond ONLY with valid JSON:
{{
  "status": "optimal|too_many|too_few",
  "recommendation": "proceed|refine|pivot",
  "reasoning": "one sentence explanation",
  "suggested_changes": [
    {{
      "filter": "company_size",
      "action": "set",
      "value": {{"min": 20, "max": 150}},
      "rationale": "why this helps"
    }}
  ],
  "estimated_impact": "how this will affect lead count",
  "confidence": "high|medium|low"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text
    
    # Extract JSON from response
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    
    return json.loads(response_text)


def apply_filter_change(filters: dict, change: dict) -> dict:
    """Apply a suggested filter change"""
    new_filters = filters.copy()
    
    filter_name = change["filter"]
    action = change["action"]
    value = change["value"]
    
    if action == "set":
        new_filters[filter_name] = value
    elif action == "add":
        if filter_name not in new_filters:
            new_filters[filter_name] = {}
        if isinstance(value, dict):
            new_filters[filter_name].update(value)
        elif isinstance(value, list):
            if filter_name not in new_filters:
                new_filters[filter_name] = []
            new_filters[filter_name].extend(value)
    elif action == "remove":
        if filter_name in new_filters:
            del new_filters[filter_name]
    
    return new_filters


# ============================================================================
# Main Refinement Loop
# ============================================================================

def main():
    print("=" * 80)
    print("ITERATIVE SEARCH REFINEMENT WITH AI")
    print("=" * 80)
    
    # Define initial goal
    goal = """
    Find CEOs and Founders at technology companies in Colorado that are:
    - Growth stage (not too small, not too large)
    - Likely to be open to sales outreach
    - In a position to make purchasing decisions
    """
    
    print(f"\nGOAL: {goal.strip()}")
    
    # Starting filters - deliberately broad
    current_filters = {
        "locations": {
            "include": [{"country": "US", "state": "CO"}],
            "exclude": []
        },
        "job_titles": {
            "include": ["CEO", "Chief Executive Officer", "Founder", "Co-Founder"],
            "exclude": ["Assistant", "Associate"]
        },
        "management_levels": ["c_level"]
    }
    
    previous_counts = []
    iteration = 1
    
    print("\n" + "=" * 80)
    print("STARTING ITERATIVE REFINEMENT")
    print("=" * 80)
    
    while iteration <= MAX_ITERATIONS:
        print(f"\n{'─' * 80}")
        print(f"ITERATION {iteration}")
        print(f"{'─' * 80}")
        
        # Preview current filters
        print("\nCurrent filters:")
        print(json.dumps(current_filters, indent=2))
        
        print("\nPreviewing search...")
        preview = preview_search(current_filters)
        count = preview.get("count", 0)
        previous_counts.append(count)
        
        print(f"\n📊 Results: {count:,} leads found")
        
        # Get AI analysis
        print("\n🤖 Getting AI analysis...")
        try:
            suggestions = get_ai_refinement_suggestions(
                current_filters,
                count,
                goal,
                iteration,
                previous_counts
            )
            
            print(f"\nStatus: {suggestions['status'].upper()}")
            print(f"Recommendation: {suggestions['recommendation'].upper()}")
            print(f"Reasoning: {suggestions['reasoning']}")
            print(f"Confidence: {suggestions['confidence'].upper()}")
            
            if suggestions.get('estimated_impact'):
                print(f"Estimated Impact: {suggestions['estimated_impact']}")
            
            # Check if we should proceed
            if suggestions['recommendation'] == 'proceed':
                print("\n✅ AI recommends proceeding with enrichment!")
                break
            
            # Check if we should pivot
            if suggestions['recommendation'] == 'pivot':
                print("\n⚠️  AI suggests pivoting strategy")
                print("Current approach may not be optimal")
                user_input = input("\nContinue anyway? (y/n): ")
                if user_input.lower() != 'y':
                    print("Refinement cancelled")
                    return
            
            # Apply suggested changes
            if suggestions.get('suggested_changes'):
                print(f"\nSuggested Changes ({len(suggestions['suggested_changes'])}):")
                for i, change in enumerate(suggestions['suggested_changes'], 1):
                    print(f"\n{i}. Filter: {change['filter']}")
                    print(f"   Action: {change['action']}")
                    print(f"   Value: {change.get('value')}")
                    print(f"   Rationale: {change['rationale']}")
                
                # Ask user to confirm
                apply = input("\nApply these changes? (y/n): ")
                if apply.lower() == 'y':
                    for change in suggestions['suggested_changes']:
                        current_filters = apply_filter_change(current_filters, change)
                    print("✓ Changes applied")
                else:
                    print("✗ Changes not applied")
                    manual = input("Enter your own filter adjustments? (y/n): ")
                    if manual.lower() != 'y':
                        break
            
        except Exception as e:
            print(f"\n❌ Error getting AI suggestions: {e}")
            print("Falling back to manual refinement")
            
            if count > 2000:
                print("\nSuggestion: Add more filters to narrow results")
                print("Options: company_size, industries, revenue_range")
            elif count < 500:
                print("\nSuggestion: Broaden filters or expand geography")
                print("Options: Add more job titles, expand to nearby states")
            else:
                print("\nLead count looks good!")
                break
        
        iteration += 1
        
        if iteration > MAX_ITERATIONS:
            print("\n⚠️  Max iterations reached")
    
    # Final decision
    print("\n" + "=" * 80)
    print("REFINEMENT COMPLETE")
    print("=" * 80)
    
    print(f"\nFinal Results:")
    print(f"  • Iterations: {iteration}")
    print(f"  • Final Count: {count:,} leads")
    print(f"  • Count History: {', '.join([f'{c:,}' for c in previous_counts])}")
    
    print(f"\nFinal Filters:")
    print(json.dumps(current_filters, indent=2))
    
    # Estimate cost
    estimated_credits = int(count * 1.5)
    estimated_cost = estimated_credits * 9 / 2000
    
    print(f"\nEstimated Enrichment Cost:")
    print(f"  • Credits: ~{estimated_credits:,}")
    print(f"  • Cost: ~${estimated_cost:.2f}")
    
    # Offer to proceed
    proceed = input("\n🚀 Proceed with enrichment? (yes/no): ").strip().lower()
    
    if proceed in ['yes', 'y']:
        print("\n⏳ Starting enrichment...")
        
        response = requests.post(
            f"{BASE_URL}/supersearch-enrichment/enrich-leads-from-supersearch",
            headers={
                "Authorization": f"Bearer {INSTANTLY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "search_filters": current_filters,
                "limit": min(count, 1000),
                "list_name": f"CO CEOs - Refined {count} leads",
                "enrichment_payload": {
                    "work_email_enrichment": True,
                    "email_verification": True,
                    "fully_enriched_profile": True,
                    "custom_flow": ["instantly"]
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Enrichment started successfully!")
            print(f"   Job ID: {data.get('id')}")
            print(f"   Resource ID: {data.get('resource_id')}")
        else:
            print(f"\n❌ Error starting enrichment: {response.status_code}")
            print(response.text)
    else:
        print("\n✗ Enrichment cancelled")
        print("\nYou can run this script again with the refined filters:")
        print(json.dumps(current_filters, indent=2))


if __name__ == "__main__":
    if INSTANTLY_API_KEY == "your_instantly_api_key_here":
        print("❌ Please set your INSTANTLY_API_KEY in the script")
        exit(1)
    
    if ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
        print("❌ Please set your ANTHROPIC_API_KEY for AI-powered refinement")
        exit(1)
    
    main()
