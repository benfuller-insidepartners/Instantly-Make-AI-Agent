# Instantly.ai SuperSearch Workflow Guide

## Overview

This guide demonstrates how to use the Instantly.ai API to:
1. **Preview searches** - Check lead counts before spending credits
2. **Refine searches** - Use AI (Claude) to improve your targeting
3. **Execute enrichments** - Run enrichment with optimal filters

## Prerequisites

```bash
pip install requests anthropic
```

## API Keys Needed

1. **Instantly.ai API Key**
   - Get it from: https://instantly.ai (Settings → API Keys)
   - Required scopes: `supersearch_enrichments:all` or `all:all`

2. **Anthropic API Key** (optional but recommended for AI-powered refinement)
   - Get it from: https://console.anthropic.com
   - Used for intelligent search filter suggestions and refinement

## Core Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. DESCRIBE YOUR IDEAL LEAD                            │
│     "Find CEOs in Colorado at tech companies..."        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  2. AI GENERATES INITIAL FILTERS                        │
│     • Locations: Colorado                               │
│     • Job Titles: CEO, Founder                          │
│     • Industries: Technology                            │
│     • Company Size: 10-200 employees                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  3. PREVIEW SEARCH (No credits spent)                   │
│     GET /preview-leads-from-supersearch                 │
│     → Returns: count = 2,847 leads                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  4. AI ANALYZES RESULTS                                 │
│     "2,847 is reasonable for enrichment"                │
│     "Suggestion: Narrow to companies with 20-100        │
│      employees for higher conversion rates"             │
└─────────────────┬───────────────────────────────────────┘
                  │
           ┌──────┴──────┐
           │             │
           ▼             ▼
    ┌──────────┐  ┌──────────┐
    │ REFINE   │  │ PROCEED  │
    │ FURTHER  │  │ TO       │
    │          │  │ ENRICH   │
    └────┬─────┘  └────┬─────┘
         │             │
         │             ▼
         │    ┌─────────────────────────────────────────┐
         │    │  5. EXECUTE ENRICHMENT                  │
         │    │     POST /enrich-leads-from-supersearch │
         │    │     • Get verified emails               │
         │    │     • Enrich profiles                   │
         │    │     • Add to campaign/list              │
         │    └─────────────────────────────────────────┘
         │
         └──────► (Loop back to step 3)
```

## Key API Endpoints

### 1. Preview Leads (No Cost)

**Endpoint:** `POST /api/v2/supersearch-enrichment/preview-leads-from-supersearch`

**Purpose:** Check how many leads match your filters WITHOUT spending credits

```python
response = requests.post(
    "https://api.instantly.ai/api/v2/supersearch-enrichment/preview-leads-from-supersearch",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "search_filters": {
            "locations": {
                "include": [{"country": "US", "state": "CO"}]
            },
            "job_titles": {
                "include": ["CEO", "Chief Executive Officer"]
            }
        }
    }
)

data = response.json()
print(f"Found {data['count']} leads")
```

**Response:**
```json
{
  "count": 2847
}
```

### 2. Enrich Leads (Consumes Credits)

**Endpoint:** `POST /api/v2/supersearch-enrichment/enrich-leads-from-supersearch`

**Purpose:** Actually fetch and enrich leads, creating a list

```python
response = requests.post(
    "https://api.instantly.ai/api/v2/supersearch-enrichment/enrich-leads-from-supersearch",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "search_filters": {...},
        "limit": 500,
        "list_name": "Colorado Tech CEOs - Jan 2026",
        "enrichment_payload": {
            "work_email_enrichment": True,
            "fully_enriched_profile": True,
            "email_verification": True,
            "technologies": True,
            "news": True,
            "funding": True,
            "custom_flow": ["instantly"]
        }
    }
)
```

**Response:**
```json
{
  "id": "enrichment-job-id",
  "resource_id": "list-id",
  "organization_id": "org-id",
  "search_filters": {...},
  "limit": 500,
  "list_name": "Colorado Tech CEOs - Jan 2026"
}
```

### 3. Check Enrichment Status

**Endpoint:** `GET /api/v2/supersearch-enrichment/{resource_id}`

```python
response = requests.get(
    f"https://api.instantly.ai/api/v2/supersearch-enrichment/{resource_id}",
    headers={"Authorization": f"Bearer {api_key}"}
)

status = response.json()
print(f"In progress: {status['in_progress']}")
print(f"Has leads: {not status['has_no_leads']}")
```

## Available Search Filters

### Location Filters
```json
{
  "locations": {
    "include": [
      {"country": "US", "state": "CO", "city": "Denver"},
      {"country": "US", "state": "CA"}
    ],
    "exclude": [
      {"city": "Los Angeles"}
    ]
  }
}
```

### Job Title Filters
```json
{
  "job_titles": {
    "include": ["CEO", "Chief Executive Officer", "Founder", "Co-Founder"],
    "exclude": ["Assistant to the CEO"]
  }
}
```

### Management & Department
```json
{
  "management_levels": ["c_level", "vp", "director"],
  "departments": ["executive", "sales", "marketing"]
}
```

### Company Filters
```json
{
  "industries": ["Technology", "SaaS", "Software"],
  "company_size": {
    "min": 10,
    "max": 500
  },
  "revenue_range": {
    "min": 1000000,
    "max": 50000000
  }
}
```

### Advanced Filters
```json
{
  "technologies": ["Salesforce", "HubSpot", "AWS"],
  "keywords": ["hiring", "recently funded", "expanding"],
  "funding_type": ["seed", "series_a", "series_b"],
  "funding_stage": ["funded"]
}
```

## Enrichment Options

### Email Enrichment
```json
{
  "work_email_enrichment": true,     // Find work emails (1-1.5 credits each)
  "email_verification": true,         // Verify emails (0.25 credits)
  "custom_flow": ["instantly"]       // Use waterfall enrichment across 5+ providers
}
```

### Profile Enrichment
```json
{
  "fully_enriched_profile": true,    // Full profile data (0.5 credits)
  "technologies": true,               // Tech stack (0.5 credits)
  "news": true,                       // Recent news (0.5 credits)
  "funding": true,                    // Funding info (0.5 credits)
  "joblisting": true                  // Job postings (0.5 credits)
}
```

### AI Enrichment
```json
{
  "ai_enrichment": {
    "model_version": "gpt-4o",
    "prompt": "Write a personalized email opener for {{first_name}} at {{company_name}}",
    "output_column": "personalized_opener",
    "input_columns": ["first_name", "company_name", "recent_news"],
    "use_instantly_credits": true,
    "overwrite": false,
    "auto_update": true
  }
}
```

## Credit Usage

| Action | Credits | Notes |
|--------|---------|-------|
| Find work email | 1.0-1.5 | Varies by provider success |
| Verify email | 0.25 | Check existing emails |
| Profile enrichment | 0.5 | Full contact/company data |
| Each optional enrichment | 0.5 | Tech, news, funding, etc. |
| AI web research | 0.5 | Web scraping agent |
| Custom AI prompt | 1.0 | Per row enrichment |
| Preview search | 0 | Free! Use liberally |

**Example:** Finding 500 CEOs with email + verification + profile + tech + news = ~1,500-2,000 credits

## AI-Powered Refinement Strategy

The AI assistant (Claude) can help in three ways:

### 1. Generate Initial Filters
```python
refiner = SearchRefiner(anthropic_api_key)
filters = refiner.suggest_filters_from_description(
    "Find CMOs at B2B SaaS companies in the Northeast with 50-200 employees"
)
```

### 2. Analyze Results
```python
result = instantly.preview_leads(filters)
analysis = refiner.analyze_search_results(result, goal_description)

print(analysis['assessment'])
# "2,847 leads is a good starting point, but you may want to narrow further..."

print(analysis['suggestions'])
# ["Add revenue filter: $5M-$50M for qualified companies",
#  "Exclude 'Coordinator' and 'Assistant' titles",
#  "Consider filtering to companies with recent news"]
```

### 3. Iterative Refinement
```python
for iteration in range(3):
    result = instantly.preview_leads(filters)
    analysis = refiner.analyze_search_results(result, goal, iteration)
    
    if analysis['proceed_with_enrichment']:
        break
    
    # Apply suggested refinements
    filters = apply_suggestions(filters, analysis['suggestions'])
```

## Best Practices

### 1. Always Preview First
```python
# ✅ GOOD: Check counts before spending credits
result = client.preview_leads(filters)
if 100 <= result.count <= 5000:
    client.enrich_leads(filters, limit=500)

# ❌ BAD: Enriching without checking
client.enrich_leads(filters, limit=10000)  # Could waste credits!
```

### 2. Start Broad, Then Narrow
```python
# Iteration 1: Broad search
filters = {"locations": {"include": [{"state": "CO"}]}}
result = client.preview_leads(filters)  # 50,000 leads - too many!

# Iteration 2: Add job titles
filters["job_titles"] = {"include": ["CEO", "Founder"]}
result = client.preview_leads(filters)  # 5,000 leads - better

# Iteration 3: Add company size
filters["company_size"] = {"min": 20, "max": 200}
result = client.preview_leads(filters)  # 1,200 leads - perfect!
```

### 3. Use AI for Complex Targeting
```python
# Instead of guessing filters, let AI help:
goal = """
Find decision-makers at healthcare technology companies in the 
Mountain West region that are likely in growth phase (20-150 employees, 
recently funded or hiring)
"""

filters = refiner.suggest_filters_from_description(goal)
# AI will suggest: location, job titles, industry, company size, keywords, etc.
```

### 4. Optimize Credit Usage
```python
# Start with minimal enrichment to test
enrichment = {
    "work_email_enrichment": True,
    "email_verification": True,
    # Skip expensive enrichments initially
}

# Once you validate the list quality, run additional enrichments
advanced_enrichment = {
    "technologies": True,
    "news": True,
    "ai_enrichment": {...}
}
```

### 5. Monitor Your Spending
```python
# Calculate expected cost before enriching
leads_count = 500
expected_credits = leads_count * 1.5  # Base email finding
expected_credits += leads_count * 0.25  # Verification
expected_credits += leads_count * 0.5  # Profile enrichment
expected_credits += leads_count * 1.0  # AI enrichment

print(f"Expected cost: ~{expected_credits:,.0f} credits")
print(f"At $9 per 2,000 credits = ${expected_credits * 9 / 2000:.2f}")
```

## Complete Working Example

```python
#!/usr/bin/env python3
"""
Find and enrich CEOs in Colorado tech companies
"""

import requests
from instantly_workflow import InstantlyAIClient, SearchRefiner

def main():
    # Initialize
    instantly = InstantlyAIClient("your_instantly_api_key")
    refiner = SearchRefiner("your_anthropic_api_key")
    
    # Step 1: AI generates filters
    goal = "Find CEOs at tech companies in Colorado with 50-200 employees"
    filters = refiner.suggest_filters_from_description(goal)
    print(f"AI-suggested filters: {filters}")
    
    # Step 2: Preview results
    result = instantly.preview_leads(filters)
    print(f"\\nFound {result.count:,} leads")
    
    # Step 3: Refine if needed
    analysis = refiner.analyze_search_results(result, goal)
    print(f"\\nAI Assessment: {analysis['assessment']}")
    
    if not analysis['proceed_with_enrichment']:
        print("\\nAI suggests refinement. Adjusting filters...")
        # Apply suggestions and preview again
        # (In production, parse and apply analysis['suggestions'])
    
    # Step 4: Enrich
    if result.count < 1000:
        enrichment = instantly.enrich_leads(
            search_filters=filters,
            limit=result.count,
            list_name="Colorado Tech CEOs",
            enrichment_options={
                "work_email_enrichment": True,
                "email_verification": True,
                "fully_enriched_profile": True,
                "custom_flow": ["instantly"]
            }
        )
        
        print(f"\\n✓ Enrichment started!")
        print(f"List: {enrichment['list_name']}")
        print(f"ID: {enrichment['id']}")

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Issue: "No leads found"
```python
# Check if filters are too restrictive
filters = {
    "locations": {"include": [{"city": "Aspen"}]},  # Very small city
    "company_size": {"min": 500, "max": 1000},      # Very specific
    "funding_stage": ["series_c"]                    # Rare
}
# Solution: Broaden one or more filters
```

### Issue: "Too many leads"
```python
# Add more specificity
filters = {
    "locations": {"include": [{"country": "US"}]},  # Too broad!
    "job_titles": {"include": ["Manager"]}          # Very common
}
# Solution: Add company size, industry, management level
```

### Issue: "Rate limit exceeded"
```python
# Space out your preview calls
import time

for filter_variation in filter_options:
    result = instantly.preview_leads(filter_variation)
    print(f"Variation: {result.count} leads")
    time.sleep(1)  # Respect rate limits
```

## Advanced Use Cases

### 1. Multi-Region Search
```python
regions = ["CO", "UT", "WY", "ID", "MT"]

for state in regions:
    filters = {
        "locations": {"include": [{"country": "US", "state": state}]},
        "job_titles": {"include": ["CEO", "Founder"]}
    }
    result = instantly.preview_leads(filters)
    print(f"{state}: {result.count} leads")
```

### 2. A/B Testing Different Personas
```python
personas = [
    {"name": "CEOs", "titles": ["CEO", "Chief Executive Officer"]},
    {"name": "Founders", "titles": ["Founder", "Co-Founder"]},
    {"name": "VPs Sales", "titles": ["VP of Sales", "SVP Sales"]}
]

for persona in personas:
    filters = {
        "locations": {"include": [{"state": "CO"}]},
        "job_titles": {"include": persona["titles"]}
    }
    result = instantly.preview_leads(filters)
    print(f"{persona['name']}: {result.count} leads")
```

### 3. Find Recently Funded Companies
```python
filters = {
    "locations": {"include": [{"state": "CO"}]},
    "funding_stage": ["funded"],
    "funding_type": ["series_a", "series_b"],
    "keywords": ["recently funded", "raised"],
    "job_titles": {"include": ["CEO", "Founder"]}
}

result = instantly.preview_leads(filters)
print(f"Found {result.count} CEOs at recently funded CO companies")
```

## Resources

- **Instantly.ai API Docs**: https://developer.instantly.ai/api/v2
- **Anthropic Claude API**: https://docs.anthropic.com
- **SuperSearch Help**: https://help.instantly.ai/en/articles/11364248-supersearch
- **Credit Pricing**: https://instantly.ai/blog/supersearch-website-visitor-roi-cost-per-lead/

## Support

If you run into issues:
1. Check API key permissions (need `supersearch_enrichments:all` scope)
2. Verify credit balance in Instantly dashboard
3. Use preview endpoint liberally - it's free!
4. Contact Instantly support: support@instantly.ai
