"""
Instantly.ai SuperSearch Workflow with LLM-Powered Refinement

This script demonstrates how to:
1. Run a supersearch preview to get lead counts
2. Use an LLM to refine and improve search filters
3. Execute enrichments once satisfied with results

Author: Claude
Date: January 2026
"""

import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import anthropic


@dataclass
class SearchResult:
    """Container for search results"""
    count: int
    search_filters: Dict[str, Any]
    raw_response: Dict[str, Any]


class InstantlyAIClient:
    """Client for interacting with Instantly.ai API"""
    
    BASE_URL = "https://api.instantly.ai/api/v2"
    
    def __init__(self, api_key: str):
        """
        Initialize the Instantly.ai client
        
        Args:
            api_key: Your Instantly.ai API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def preview_leads(self, search_filters: Dict[str, Any]) -> SearchResult:
        """
        Preview leads from a SuperSearch without actually enriching them.
        This is useful to check lead counts before committing credits.
        
        Args:
            search_filters: Dictionary of search filters
            
        Returns:
            SearchResult object with count and filters
        """
        url = f"{self.BASE_URL}/supersearch-enrichment/preview-leads-from-supersearch"
        
        payload = {
            "search_filters": search_filters
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return SearchResult(
            count=data.get("count", 0),
            search_filters=search_filters,
            raw_response=data
        )
    
    def enrich_leads(
        self,
        search_filters: Dict[str, Any],
        limit: int = 100,
        list_name: Optional[str] = None,
        resource_id: Optional[str] = None,
        enrichment_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Actually enrich and import leads from SuperSearch.
        This will consume credits and create/populate a list.
        
        Args:
            search_filters: Dictionary of search filters
            limit: Maximum number of leads to enrich
            list_name: Name for the new list (if not using resource_id)
            resource_id: ID of existing list/campaign to add to
            enrichment_options: Enrichment settings (email, profile, AI, etc.)
            
        Returns:
            Dictionary with enrichment job details
        """
        url = f"{self.BASE_URL}/supersearch-enrichment/enrich-leads-from-supersearch"
        
        payload = {
            "search_filters": search_filters,
            "limit": limit
        }
        
        if list_name:
            payload["list_name"] = list_name
        
        if resource_id:
            payload["resource_id"] = resource_id
        
        if enrichment_options:
            payload["enrichment_payload"] = enrichment_options
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_enrichment_status(self, resource_id: str) -> Dict[str, Any]:
        """
        Check the status of an enrichment job
        
        Args:
            resource_id: ID of the list/campaign being enriched
            
        Returns:
            Dictionary with enrichment status details
        """
        url = f"{self.BASE_URL}/supersearch-enrichment/{resource_id}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()


class SearchRefiner:
    """Uses an LLM to help refine and improve search filters"""
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize the search refiner with optional Anthropic API key
        
        Args:
            anthropic_api_key: Your Anthropic API key (optional)
        """
        self.client = anthropic.Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None
    
    def analyze_search_results(
        self,
        search_result: SearchResult,
        goal_description: str,
        current_iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Use Claude to analyze search results and suggest refinements
        
        Args:
            search_result: The SearchResult from preview
            goal_description: What you're trying to achieve
            current_iteration: Which refinement iteration this is
            
        Returns:
            Dictionary with analysis and suggested refinements
        """
        if not self.client:
            print("No Anthropic API key provided - returning manual refinement prompt")
            return self._manual_refinement_prompt(search_result, goal_description)
        
        prompt = f"""I'm using Instantly.ai's SuperSearch to find leads. Here's my situation:

GOAL: {goal_description}

CURRENT SEARCH FILTERS:
{json.dumps(search_result.search_filters, indent=2)}

RESULTS: Found {search_result.count:,} leads

ITERATION: #{current_iteration}

Please analyze these results and provide:
1. Assessment: Is the lead count appropriate? (Too few? Too many? Just right?)
2. Filter Quality: Are the current filters well-targeted for the goal?
3. Refinements: Suggest specific improvements to the search filters
4. Next Steps: Should I proceed with enrichment or refine further?

Available filter types in Instantly.ai:
- locations (include/exclude with city, state, country)
- job_titles (include/exclude)
- departments (e.g., "executive", "sales", "marketing")
- management_levels (e.g., "c_level", "vp", "director")
- industries
- company_size (min/max employee count)
- revenue_range (min/max)
- technologies (software/tools used)
- keywords (in job descriptions or company info)
- funding_type, funding_stage

Provide your response as structured JSON with:
- assessment: string
- suggestions: array of specific filter changes
- proceed_with_enrichment: boolean
- reasoning: string
"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Try to extract JSON if it's wrapped in markdown
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            analysis = json.loads(response_text)
            return analysis
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return self._manual_refinement_prompt(search_result, goal_description)
    
    def _manual_refinement_prompt(
        self,
        search_result: SearchResult,
        goal_description: str
    ) -> Dict[str, Any]:
        """Fallback manual refinement when no API key available"""
        return {
            "assessment": f"Found {search_result.count:,} leads matching your criteria",
            "suggestions": [
                "Review the current filters manually",
                "Consider if the lead count aligns with your goals",
                "Adjust location, job title, or company size filters as needed"
            ],
            "proceed_with_enrichment": search_result.count > 0 and search_result.count < 10000,
            "reasoning": "Manual review recommended - no AI analysis available"
        }
    
    def suggest_filters_from_description(self, description: str) -> Dict[str, Any]:
        """
        Generate initial search filters from a natural language description
        
        Args:
            description: Natural language description of target audience
            
        Returns:
            Dictionary of suggested search filters
        """
        if not self.client:
            print("No Anthropic API key - please create filters manually")
            return {}
        
        prompt = f"""Convert this natural language lead description into Instantly.ai search filters:

"{description}"

Available filter types:
- locations: {{include: [{{"country": "US", "state": "CO"}}], exclude: []}}
- job_titles: {{include: ["CEO", "Chief Executive Officer"], exclude: []}}
- departments: ["executive", "sales", "marketing", "engineering", "operations"]
- management_levels: ["c_level", "vp", "director", "manager"]
- industries: ["Technology", "SaaS", "Healthcare", etc.]
- company_size: {{min: 10, max: 500}}
- revenue_range: {{min: 1000000, max: 50000000}}
- technologies: ["Salesforce", "HubSpot", etc.]
- keywords: ["hiring", "recently funded", etc.]

Provide a JSON object with appropriate filters for this search. Only include filters that are clearly relevant.
"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            filters = json.loads(response_text)
            return filters
            
        except Exception as e:
            print(f"Error generating filters: {e}")
            return {}


def run_workflow_example():
    """
    Example workflow: Find CEOs in Colorado with LLM-assisted refinement
    """
    
    # Configuration
    INSTANTLY_API_KEY = "your_instantly_api_key_here"
    ANTHROPIC_API_KEY = "your_anthropic_api_key_here"  # Optional but recommended
    
    # Initialize clients
    instantly = InstantlyAIClient(INSTANTLY_API_KEY)
    refiner = SearchRefiner(ANTHROPIC_API_KEY)
    
    # Step 1: Generate initial filters from natural language
    print("=" * 60)
    print("STEP 1: Generating Initial Search Filters")
    print("=" * 60)
    
    goal = "Find CEOs and founders of technology companies in Colorado with 10-200 employees"
    print(f"\nGoal: {goal}\n")
    
    # Get AI-suggested filters
    initial_filters = refiner.suggest_filters_from_description(goal)
    print("Initial filters suggested by AI:")
    print(json.dumps(initial_filters, indent=2))
    
    # Or define manually:
    manual_filters = {
        "locations": {
            "include": [
                {"country": "US", "state": "CO"}
            ],
            "exclude": []
        },
        "job_titles": {
            "include": ["CEO", "Chief Executive Officer", "Founder", "Co-Founder"],
            "exclude": []
        },
        "management_levels": ["c_level"],
        "industries": ["Technology", "Software", "SaaS"],
        "company_size": {
            "min": 10,
            "max": 200
        }
    }
    
    # Use manual or AI-suggested (fallback to manual if AI failed)
    search_filters = initial_filters if initial_filters else manual_filters
    
    # Step 2: Preview leads
    print("\n" + "=" * 60)
    print("STEP 2: Preview Search Results")
    print("=" * 60)
    
    result = instantly.preview_leads(search_filters)
    print(f"\nFound {result.count:,} leads matching criteria")
    
    # Step 3: Refine with AI assistance
    print("\n" + "=" * 60)
    print("STEP 3: AI-Assisted Refinement")
    print("=" * 60)
    
    max_iterations = 3
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")
        
        # Get AI analysis
        analysis = refiner.analyze_search_results(result, goal, iteration)
        
        print(f"\nAssessment: {analysis['assessment']}")
        print(f"\nReasoning: {analysis['reasoning']}")
        
        if analysis.get('suggestions'):
            print("\nSuggested refinements:")
            for i, suggestion in enumerate(analysis['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
        if analysis.get('proceed_with_enrichment'):
            print("\n✓ AI recommends proceeding with enrichment")
            break
        
        # Apply refinements (in a real implementation, you'd parse the suggestions
        # and modify search_filters accordingly)
        print("\n⚠ AI suggests further refinement")
        
        # For demonstration, let's manually adjust and re-preview
        # In production, you'd implement logic to apply AI suggestions automatically
        user_input = input("\nApply suggested changes and continue? (y/n): ")
        if user_input.lower() != 'y':
            break
        
        # Example: Adjust filters based on AI feedback
        # This is where you'd implement the actual filter modifications
        # search_filters = apply_refinements(search_filters, analysis['suggestions'])
        
        # Re-preview with updated filters
        # result = instantly.preview_leads(search_filters)
        # print(f"\nUpdated results: {result.count:,} leads")
    
    # Step 4: Execute enrichment
    print("\n" + "=" * 60)
    print("STEP 4: Execute Enrichment")
    print("=" * 60)
    
    proceed = input(f"\nProceed with enriching {result.count:,} leads? (y/n): ")
    
    if proceed.lower() == 'y':
        # Configure enrichment options
        enrichment_options = {
            "work_email_enrichment": True,
            "fully_enriched_profile": True,
            "email_verification": True,
            "technologies": True,
            "news": True,
            "funding": True,
            # AI enrichment example
            "ai_enrichment": {
                "model_version": "gpt-4o",
                "prompt": "Write a personalized opening line for {{first_name}} at {{company_name}} based on recent company news",
                "output_column": "personalized_opener",
                "input_columns": ["first_name", "company_name", "recent_news"]
            },
            "custom_flow": ["instantly"]  # Use Instantly's waterfall enrichment
        }
        
        list_name = f"CO Tech CEOs - {result.count} leads"
        
        print(f"\nStarting enrichment for list: {list_name}")
        print("Enrichment options:")
        print(json.dumps(enrichment_options, indent=2))
        
        enrichment_job = instantly.enrich_leads(
            search_filters=search_filters,
            limit=min(result.count, 1000),  # Limit to 1000 for safety
            list_name=list_name,
            enrichment_options=enrichment_options
        )
        
        print("\n✓ Enrichment job started!")
        print(f"Resource ID: {enrichment_job.get('resource_id')}")
        print(f"Job ID: {enrichment_job.get('id')}")
        
        # Monitor status
        if enrichment_job.get('resource_id'):
            print("\nMonitoring enrichment status...")
            status = instantly.get_enrichment_status(enrichment_job['resource_id'])
            print(f"In Progress: {status.get('in_progress')}")
            print(f"Has Leads: {not status.get('has_no_leads')}")
    else:
        print("\n✗ Enrichment cancelled")
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)


def quick_example():
    """
    Quick example showing the basic workflow without all the refinement
    """
    INSTANTLY_API_KEY = "your_api_key_here"
    
    client = InstantlyAIClient(INSTANTLY_API_KEY)
    
    # Define search
    filters = {
        "locations": {
            "include": [{"country": "US", "state": "CO"}]
        },
        "job_titles": {
            "include": ["CEO", "Chief Executive Officer"]
        },
        "management_levels": ["c_level"]
    }
    
    # Preview
    result = client.preview_leads(filters)
    print(f"Found {result.count:,} CEOs in Colorado")
    
    # Enrich if count looks good
    if 100 <= result.count <= 5000:
        job = client.enrich_leads(
            search_filters=filters,
            limit=500,
            list_name="Colorado CEOs"
        )
        print(f"Enrichment started: {job['id']}")
    else:
        print("Lead count outside target range - refine filters")


if __name__ == "__main__":
    # Uncomment to run the full workflow
    # run_workflow_example()
    
    # Or run the quick example
    # quick_example()
    
    print(__doc__)
    print("\nTo use this script:")
    print("1. Install dependencies: pip install requests anthropic")
    print("2. Set your API keys in the script")
    print("3. Uncomment and run run_workflow_example() or quick_example()")
