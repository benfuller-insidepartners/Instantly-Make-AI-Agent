#!/usr/bin/env python3
"""
Simple Example: Find CEOs in Colorado

This script demonstrates the complete workflow:
1. Preview search results (free)
2. Get AI recommendations
3. Enrich leads (costs credits)

Usage:
    python simple_example.py
"""

import requests
import json
import anthropic


# ============================================================================
# CONFIGURATION - Update these with your API keys
# ============================================================================
INSTANTLY_API_KEY = "your_instantly_api_key_here"
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"  # Optional but recommended

BASE_URL = "https://api.instantly.ai/api/v2"


# ============================================================================
# STEP 1: Define Your Search
# ============================================================================

print("=" * 70)
print("STEP 1: DEFINING SEARCH FOR CEOS IN COLORADO")
print("=" * 70)

# Basic search filters
search_filters = {
    "locations": {
        "include": [
            {"country": "US", "state": "CO"}
        ],
        "exclude": []
    },
    "job_titles": {
        "include": [
            "CEO",
            "Chief Executive Officer",
            "Founder",
            "Co-Founder",
            "President"
        ],
        "exclude": [
            "Assistant to the CEO",
            "Executive Assistant"
        ]
    },
    "management_levels": ["c_level"],
    "company_size": {
        "min": 10,
        "max": 500
    }
}

print("\nSearch Filters:")
print(json.dumps(search_filters, indent=2))


# ============================================================================
# STEP 2: Preview Search Results (FREE - No Credits Used)
# ============================================================================

print("\n" + "=" * 70)
print("STEP 2: PREVIEWING SEARCH RESULTS (No cost)")
print("=" * 70)

headers = {
    "Authorization": f"Bearer {INSTANTLY_API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{BASE_URL}/supersearch-enrichment/preview-leads-from-supersearch",
    headers=headers,
    json={"search_filters": search_filters}
)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
    exit(1)

preview_data = response.json()
lead_count = preview_data.get("count", 0)

print(f"\n✓ Found {lead_count:,} leads matching your criteria")


# ============================================================================
# STEP 3: AI Analysis and Recommendations (Optional)
# ============================================================================

print("\n" + "=" * 70)
print("STEP 3: AI ANALYSIS")
print("=" * 70)

if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_anthropic_api_key_here":
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = f"""Analyze this lead search result:

Search Goal: Find CEOs at companies in Colorado
Current Filters: {json.dumps(search_filters, indent=2)}
Results: {lead_count:,} leads found

Provide a brief analysis:
1. Is the lead count appropriate? (Too few, too many, or just right?)
2. What's the estimated cost? (Assume 1.5 credits per lead for email + verification)
3. Should we proceed or refine the search?
4. If refining, suggest 2-3 specific filter adjustments

Keep your response concise and actionable."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        ai_analysis = message.content[0].text
        print("\n🤖 Claude's Analysis:")
        print(ai_analysis)
        
    except Exception as e:
        print(f"\n⚠️  Could not get AI analysis: {e}")
        print("Proceeding without AI recommendations...")
else:
    print("\n⚠️  No Anthropic API key provided - skipping AI analysis")
    print(f"Manual assessment: {lead_count:,} leads found")
    
    if lead_count == 0:
        print("❌ No leads found - filters may be too restrictive")
        exit(1)
    elif lead_count > 10000:
        print("⚠️  Large result set - consider narrowing filters to save credits")
    else:
        print("✓ Lead count looks reasonable")


# ============================================================================
# STEP 4: User Decision Point
# ============================================================================

print("\n" + "=" * 70)
print("STEP 4: ENRICHMENT DECISION")
print("=" * 70)

estimated_credits = int(lead_count * 1.5)  # Rough estimate
estimated_cost = estimated_credits * 9 / 2000  # $9 per 2000 credits

print(f"\nEstimated Cost for {lead_count:,} leads:")
print(f"  • Credits: ~{estimated_credits:,}")
print(f"  • USD: ~${estimated_cost:.2f}")
print(f"\nThis includes:")
print(f"  • Work email enrichment")
print(f"  • Email verification")

proceed = input("\nProceed with enrichment? (yes/no): ").strip().lower()

if proceed not in ['yes', 'y']:
    print("\n✗ Enrichment cancelled")
    print("\nTo refine your search:")
    print("1. Adjust the search_filters in the script")
    print("2. Run the script again to preview")
    print("3. Repeat until satisfied")
    exit(0)


# ============================================================================
# STEP 5: Execute Enrichment (COSTS CREDITS)
# ============================================================================

print("\n" + "=" * 70)
print("STEP 5: EXECUTING ENRICHMENT")
print("=" * 70)

# Configure enrichment options
enrichment_payload = {
    "work_email_enrichment": True,
    "email_verification": True,
    "fully_enriched_profile": True,
    "custom_flow": ["instantly"]  # Use Instantly's waterfall enrichment
}

# Set a reasonable limit (max 1000 for this example)
enrichment_limit = min(lead_count, 1000)

list_name = f"Colorado CEOs - {lead_count} leads"

print(f"\nStarting enrichment...")
print(f"  • List name: {list_name}")
print(f"  • Leads to enrich: {enrichment_limit:,}")
print(f"  • Enrichment options:")
print(f"    - Work email enrichment: ✓")
print(f"    - Email verification: ✓")
print(f"    - Full profile: ✓")

enrichment_response = requests.post(
    f"{BASE_URL}/supersearch-enrichment/enrich-leads-from-supersearch",
    headers=headers,
    json={
        "search_filters": search_filters,
        "limit": enrichment_limit,
        "list_name": list_name,
        "enrichment_payload": enrichment_payload
    }
)

if enrichment_response.status_code != 200:
    print(f"\n❌ Error starting enrichment: {enrichment_response.status_code}")
    print(enrichment_response.text)
    exit(1)

enrichment_data = enrichment_response.json()

print("\n✅ Enrichment job started successfully!")
print(f"\nJob Details:")
print(f"  • Job ID: {enrichment_data.get('id')}")
print(f"  • Resource ID: {enrichment_data.get('resource_id')}")
print(f"  • Organization ID: {enrichment_data.get('organization_id')}")


# ============================================================================
# STEP 6: Check Status (Optional)
# ============================================================================

print("\n" + "=" * 70)
print("STEP 6: CHECKING STATUS")
print("=" * 70)

resource_id = enrichment_data.get('resource_id')

if resource_id:
    status_response = requests.get(
        f"{BASE_URL}/supersearch-enrichment/{resource_id}",
        headers=headers
    )
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        
        print(f"\nEnrichment Status:")
        print(f"  • In Progress: {status_data.get('in_progress')}")
        print(f"  • Has Leads: {not status_data.get('has_no_leads')}")
        print(f"  • Resource Type: {status_data.get('resource_type')}")
        
        if status_data.get('in_progress'):
            print(f"\n⏳ Enrichment is still running...")
            print(f"   Check your Instantly dashboard for updates")
        else:
            print(f"\n✓ Enrichment complete!")
            print(f"   View your list in Instantly: https://app.instantly.ai")
    else:
        print(f"\n⚠️  Could not fetch status: {status_response.status_code}")


# ============================================================================
# STEP 7: Summary
# ============================================================================

print("\n" + "=" * 70)
print("ENRICHMENT COMPLETE - SUMMARY")
print("=" * 70)

print(f"""
✓ Successfully enriched {enrichment_limit:,} Colorado CEOs

Next Steps:
1. Log into Instantly: https://app.instantly.ai
2. Navigate to your lists
3. Find list: "{list_name}"
4. Review and export your enriched leads

What you got:
• Verified work emails
• Full contact profiles
• LinkedIn URLs
• Company information

You can now:
• Add these leads to a campaign
• Export to your CRM
• Download as CSV
• Further enrich with AI prompts
""")

print("=" * 70)
