# Building an Instantly.ai AI Agent in Make.com

## Overview

This guide shows you how to create an AI-powered Make scenario that:
1. Takes a natural language goal as input
2. Uses AI to generate search filters
3. Previews results and iteratively refines
4. Executes enrichment when optimal
5. Returns results to you

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MAKE SCENARIO FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. [Webhook/Form] ──────► User Input                      │
│         │                   "Find CEOs in Colorado..."      │
│         │                                                   │
│         ▼                                                   │
│  2. [Claude/OpenAI] ─────► Generate Initial Filters        │
│         │                   {locations, job_titles...}      │
│         │                                                   │
│         ▼                                                   │
│  3. [HTTP] ──────────────► Preview Search (Instantly)      │
│         │                   GET lead count                  │
│         │                                                   │
│         ▼                                                   │
│  4. [Router] ────────────► Check Lead Count                │
│         │                                                   │
│    ┌────┴────┬──────────┬──────────┐                       │
│    ▼         ▼          ▼          ▼                        │
│  Too Few  Too Many  Just Right  Max Iterations              │
│    │         │          │          │                        │
│    ▼         ▼          │          │                        │
│  [AI Refine]───────────►│          │                        │
│    │                    │          │                        │
│    └────────────────────┘          │                        │
│         │                           │                        │
│         └──► [Repeater] ◄───────────┘                       │
│              (Max 5 iterations)                             │
│                    │                                         │
│                    ▼                                         │
│  5. [HTTP] ──────────────► Execute Enrichment              │
│         │                   (if approved)                   │
│         │                                                   │
│         ▼                                                   │
│  6. [Email/Slack] ───────► Notify User                     │
│         │                   "Enrichment complete!"          │
│         │                                                   │
│         ▼                                                   │
│  7. [Google Sheets] ─────► Log Results                     │
│                            (optional)                        │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Make Modules
- HTTP module (built-in)
- Anthropic Claude module OR OpenAI module
- Iterator/Repeater (built-in)
- Router (built-in)
- Tools > Set Variable (built-in)

### API Keys Needed
1. **Instantly.ai API Key**
   - Store in Make: Connections → Add → HTTP → Bearer Token
   - Name it: "Instantly API"

2. **Anthropic API Key**
   - Store in Make: Connections → Add → Anthropic
   - Name it: "Claude API"

## Step-by-Step Build

### Module 1: Webhook Trigger (Start)

**Module:** Webhooks → Custom Webhook

**Configuration:**
```json
{
  "name": "Instantly Lead Finder",
  "parameters": [
    {
      "name": "goal",
      "type": "text",
      "required": true,
      "label": "Search Goal",
      "help": "Describe your ideal leads"
    },
    {
      "name": "target_count_min",
      "type": "number",
      "default": 500
    },
    {
      "name": "target_count_max",
      "type": "number",
      "default": 2000
    },
    {
      "name": "auto_enrich",
      "type": "boolean",
      "default": false,
      "label": "Auto-enrich when optimal?"
    }
  ]
}
```

**Test Payload:**
```json
{
  "goal": "Find CEOs at technology companies in Colorado with 50-200 employees",
  "target_count_min": 500,
  "target_count_max": 2000,
  "auto_enrich": false
}
```

---

### Module 2: AI - Generate Initial Filters

**Module:** Anthropic Claude → Create a Completion

**Configuration:**

**Model:** `claude-sonnet-4-20250514`

**System Prompt:**
```
You are a lead generation expert helping to create search filters for Instantly.ai SuperSearch.

Convert natural language goals into precise search filter JSON.

Available filters:
- locations: {include: [{country, state?, city?}], exclude: []}
- job_titles: {include: [], exclude: []}
- management_levels: ["c_level", "vp", "director", "manager"]
- departments: ["executive", "sales", "marketing", "engineering", "operations"]
- industries: ["Technology", "SaaS", "Healthcare", etc.]
- company_size: {min: number, max: number}
- revenue_range: {min: number, max: number}
- technologies: ["Salesforce", "HubSpot", etc.]
- keywords: ["hiring", "funded", "growing"]
- funding_stage: ["funded", "unfunded"]
- funding_type: ["seed", "series_a", "series_b"]

Return ONLY valid JSON with no markdown formatting.
```

**User Prompt:**
```
Goal: {{1.goal}}

Generate optimal search filters for this goal. Be specific but not overly restrictive.
Return as pure JSON with no explanation or markdown.
```

**Max Tokens:** 1500

**Output:** Save to variable `initial_filters`

**Parse Response:**
Add a "Parse JSON" module after this:
- **Module:** Tools → Parse JSON
- **JSON String:** `{{2.output}}`
- **Data Structure:** (Auto-generate from example)

---

### Module 3: Set Variables (Initialize Loop)

**Module:** Tools → Set Multiple Variables

**Variables:**
```json
{
  "iteration": 1,
  "max_iterations": 5,
  "current_filters": "{{3.output}}",
  "lead_counts": [],
  "proceed_with_enrichment": false,
  "target_min": "{{1.target_count_min}}",
  "target_max": "{{1.target_count_max}}"
}
```

---

### Module 4: Repeater (Refinement Loop)

**Module:** Flow Control → Repeater

**Configuration:**
- **Repeats:** `{{4.max_iterations}}`
- **Condition:** Stop when `{{proceed_with_enrichment}}` is true

---

### Module 5: Preview Search (Inside Repeater)

**Module:** HTTP → Make a Request

**Configuration:**

**URL:** `https://api.instantly.ai/api/v2/supersearch-enrichment/preview-leads-from-supersearch`

**Method:** POST

**Headers:**
```json
{
  "Authorization": "Bearer {{connection.instantly_api_key}}",
  "Content-Type": "application/json"
}
```

**Body Type:** Raw

**Request Content:**
```json
{
  "search_filters": {{4.current_filters}}
}
```

**Parse Response:** Yes

**Output:** Save `count` field to variable

---

### Module 6: Add Count to History

**Module:** Tools → Set Variable

**Variable Name:** `lead_counts`

**Value:** 
```
{{array(4.lead_counts; 5.data.count)}}
```

This appends the new count to the history array.

---

### Module 7: Router - Check Lead Count

**Module:** Flow Control → Router

**Routes:**

#### Route 1: Too Few Leads
**Filter:** `{{5.data.count}} < {{4.target_min}}`
**Action:** Go to "AI Refine - Broaden" module

#### Route 2: Too Many Leads
**Filter:** `{{5.data.count}} > {{4.target_max}}`
**Action:** Go to "AI Refine - Narrow" module

#### Route 3: Optimal Range
**Filter:** `{{5.data.count}} >= {{4.target_min}} AND {{5.data.count}} <= {{4.target_max}}`
**Action:** Go to "Set Proceed Flag" module

#### Route 4: Max Iterations (Fallback)
**Filter:** `{{4.iteration}} = {{4.max_iterations}}`
**Action:** Go to "Max Iterations Warning" module

---

### Module 8a: AI Refine - Narrow (Route 2)

**Module:** Anthropic Claude → Create a Completion

**System Prompt:**
```
You are refining lead search filters. The current search returned too many results.

Your task: Suggest ONE filter modification to narrow the results.

Current filters:
{{4.current_filters}}

Current count: {{5.data.count}}
Target range: {{4.target_min}} to {{4.target_max}}
Iteration: {{4.iteration}} of {{4.max_iterations}}

Respond with ONLY JSON (no markdown):
{
  "modified_filters": {...complete filter object...},
  "change_description": "brief explanation",
  "estimated_new_count": number
}
```

**User Prompt:** (empty, all in system prompt)

**Output:** Parse JSON and set `current_filters` to `modified_filters`

---

### Module 8b: AI Refine - Broaden (Route 1)

**Module:** Anthropic Claude → Create a Completion

**System Prompt:**
```
You are refining lead search filters. The current search returned too few results.

Your task: Suggest ONE filter modification to broaden the results.

Current filters:
{{4.current_filters}}

Current count: {{5.data.count}}
Target range: {{4.target_min}} to {{4.target_max}}
Iteration: {{4.iteration}} of {{4.max_iterations}}

Options to broaden:
- Expand geographic area
- Add more job titles
- Increase company size range
- Remove restrictive filters

Respond with ONLY JSON (no markdown):
{
  "modified_filters": {...complete filter object...},
  "change_description": "brief explanation",
  "estimated_new_count": number
}
```

**Output:** Parse JSON and set `current_filters` to `modified_filters`

---

### Module 8c: Set Proceed Flag (Route 3)

**Module:** Tools → Set Variable

**Variable Name:** `proceed_with_enrichment`
**Value:** `true`

This will break the Repeater loop.

---

### Module 8d: Max Iterations Warning (Route 4)

**Module:** Tools → Set Variable

**Variable Name:** `proceed_with_enrichment`
**Value:** `true`

**Variable Name:** `warning_message`
**Value:** `"Max iterations reached with {{5.data.count}} leads. Proceeding with current filters."`

---

### Module 9: Increment Iteration

**Module:** Tools → Set Variable

**Variable Name:** `iteration`
**Value:** `{{add(4.iteration; 1)}}`

This runs at the end of each loop iteration.

---

### Module 10: Router - Auto Enrich Decision

**Module:** Flow Control → Router

**Routes:**

#### Route 1: Auto-Enrich Enabled
**Filter:** `{{1.auto_enrich}} = true`
**Action:** Go directly to Enrichment module

#### Route 2: Manual Approval
**Filter:** `{{1.auto_enrich}} = false`
**Action:** Go to Email/Slack approval module

---

### Module 11a: Request Approval (Route 2)

**Module:** Email → Send an Email (or Slack → Send a Message)

**To:** Your email
**Subject:** `Instantly Lead Search Ready - {{5.data.count}} leads found`

**Body:**
```
Search refinement complete!

Goal: {{1.goal}}

Final Results:
• Lead Count: {{5.data.count}}
• Iterations: {{4.iteration}}
• Filters: {{4.current_filters}}

Estimated Cost:
• Credits: ~{{multiply(5.data.count; 1.5)}}
• USD: ~${{divide(multiply(5.data.count; 1.5); 222)}}

Final Filters:
{{formatJSON(4.current_filters)}}

Reply "YES" to proceed with enrichment.

Approve enrichment here: {{scenario.webhook_url}}/approve?job_id={{generate_uuid()}}
```

---

### Module 11b: Wait for Approval

**Module:** Webhooks → Custom Webhook Response

**Webhook URL:** `/approve`

**Parameters:**
- job_id
- approved (boolean)

**Timeout:** 1 hour

---

### Module 12: Execute Enrichment

**Module:** HTTP → Make a Request

**URL:** `https://api.instantly.ai/api/v2/supersearch-enrichment/enrich-leads-from-supersearch`

**Method:** POST

**Headers:**
```json
{
  "Authorization": "Bearer {{connection.instantly_api_key}}",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "search_filters": {{4.current_filters}},
  "limit": {{min(5.data.count; 1000)}},
  "list_name": "{{formatDate(now; 'YYYY-MM-DD')}} - {{1.goal}} ({{5.data.count}} leads)",
  "enrichment_payload": {
    "work_email_enrichment": true,
    "email_verification": true,
    "fully_enriched_profile": true,
    "custom_flow": ["instantly"]
  }
}
```

**Parse Response:** Yes

---

### Module 13: Get Enrichment Status

**Module:** HTTP → Make a Request

**URL:** `https://api.instantly.ai/api/v2/supersearch-enrichment/{{12.data.resource_id}}`

**Method:** GET

**Headers:**
```json
{
  "Authorization": "Bearer {{connection.instantly_api_key}}"
}
```

---

### Module 14: Log to Google Sheets (Optional)

**Module:** Google Sheets → Add a Row

**Spreadsheet:** "Instantly Lead Searches"

**Sheet:** "Search Log"

**Values:**
```
Timestamp: {{now}}
Goal: {{1.goal}}
Final Count: {{5.data.count}}
Iterations: {{4.iteration}}
Filters: {{4.current_filters}}
Enrichment ID: {{12.data.id}}
Resource ID: {{12.data.resource_id}}
Status: {{if(13.data.in_progress; "In Progress"; "Complete")}}
Estimated Credits: {{multiply(5.data.count; 1.5)}}
```

---

### Module 15: Send Success Notification

**Module:** Email → Send an Email

**To:** Your email
**Subject:** `✅ Instantly Enrichment Complete - {{5.data.count}} leads`

**Body:**
```html
<h2>Enrichment Complete!</h2>

<p><strong>Goal:</strong> {{1.goal}}</p>

<h3>Results:</h3>
<ul>
  <li>Leads Found: {{5.data.count}}</li>
  <li>Leads Enriched: {{min(5.data.count; 1000)}}</li>
  <li>Refinement Iterations: {{4.iteration}}</li>
  <li>Credits Used: ~{{multiply(min(5.data.count; 1000); 1.5)}}</li>
</ul>

<h3>Enrichment Details:</h3>
<ul>
  <li>Job ID: {{12.data.id}}</li>
  <li>Resource ID: {{12.data.resource_id}}</li>
  <li>List Name: {{12.data.list_name}}</li>
</ul>

<h3>Final Filters:</h3>
<pre>{{formatJSON(4.current_filters)}}</pre>

<p><a href="https://app.instantly.ai">View in Instantly →</a></p>
```

---

## Advanced Features

### 1. Add Scheduling

Add a Schedule trigger before the webhook:
- **Module:** Schedule → Every Day at 9 AM
- **Flow:** Schedule → Generate Default Goals → Run Searches

### 2. Add Error Handling

Wrap key modules in Error Handlers:

**HTTP Error Handler:**
```
If 429 (Rate Limit):
  - Wait 60 seconds
  - Retry request

If 401 (Auth Error):
  - Send alert
  - Stop scenario

If 500 (Server Error):
  - Log error
  - Continue with fallback
```

### 3. Add Data Store Integration

**Module:** Data Store → Search and Create Record

Store search history:
```json
{
  "goal": "{{1.goal}}",
  "timestamp": "{{now}}",
  "final_count": "{{5.data.count}}",
  "filters": "{{4.current_filters}}",
  "iterations": "{{4.iteration}}",
  "enrichment_id": "{{12.data.id}}"
}
```

Query before searching:
```
Search for similar goals in the last 30 days
If found: Use those filters as starting point
```

### 4. Add Credit Monitoring

Before enrichment, check credit balance:

**Module:** HTTP → Make a Request (if Instantly has this endpoint)

**Logic:**
```
If credits < estimated_cost:
  - Send alert
  - Stop enrichment
  - Request credit top-up
```

---

## Configuration Tips

### 1. Optimize AI Prompts

**Good Prompt Structure:**
```
Role: You are a [specific role]
Task: [one clear task]
Context: [relevant data]
Constraints: [what to avoid]
Output: [exact format needed]
```

**Bad Prompt:**
```
"Refine the search filters"
```

**Good Prompt:**
```
"You are refining lead search filters. Current count is {{count}} but target is {{target}}. Suggest ONE specific filter change to narrow results. Return only JSON."
```

### 2. Handle AI Response Parsing

Always add these modules after AI:

1. **Text Parser → Replace**
   - Pattern: ```json and ```
   - Replace with: (empty)

2. **Tools → Parse JSON**
   - String: {{cleaned_response}}

3. **Error Handler:**
   - If parse fails: Log error and use fallback

### 3. Use Variables Effectively

**Module-Level Variables:**
- Store temporary data between modules
- Clear at start of each loop

**Scenario-Level Variables:**
- Store data that persists across runs
- Use Data Store for long-term storage

### 4. Rate Limit Protection

Add delays between API calls:

**Module:** Tools → Sleep
- **Delay:** 1 second
- **Position:** After each HTTP request

### 5. Testing Strategy

**Test Each Module Individually:**
1. Turn off auto-execution
2. Run module with test data
3. Verify output format
4. Continue to next module

**Test Full Scenario:**
1. Use webhook test data
2. Monitor each module execution
3. Check variable values
4. Verify final output

---

## Complete Scenario Blueprint

Here's the JSON blueprint you can import into Make:

```json
{
  "name": "Instantly AI Lead Finder",
  "flow": [
    {
      "id": 1,
      "module": "webhook",
      "version": 1,
      "parameters": {
        "hook": "instantly_lead_finder"
      }
    },
    {
      "id": 2,
      "module": "anthropic:completion",
      "version": 1,
      "parameters": {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "system": "You are a lead generation expert...",
        "messages": [
          {
            "role": "user",
            "content": "Goal: {{1.goal}}"
          }
        ]
      },
      "mapper": {
        "model": "claude-sonnet-4-20250514",
        "system": "{{system_prompt}}",
        "messages": "{{messages}}"
      }
    },
    {
      "id": 3,
      "module": "json:ParseJSON",
      "version": 1,
      "parameters": {},
      "mapper": {
        "json": "{{2.output}}"
      }
    },
    {
      "id": 4,
      "module": "builtin:SetVariables",
      "version": 1,
      "parameters": {},
      "mapper": {
        "variables": [
          {
            "name": "iteration",
            "value": 1
          },
          {
            "name": "current_filters",
            "value": "{{3.output}}"
          },
          {
            "name": "lead_counts",
            "value": "[]"
          }
        ]
      }
    },
    {
      "id": 5,
      "module": "builtin:Repeater",
      "version": 1,
      "parameters": {
        "repeats": 5
      }
    },
    {
      "id": 6,
      "module": "http:ActionSendData",
      "version": 3,
      "parameters": {},
      "mapper": {
        "url": "https://api.instantly.ai/api/v2/supersearch-enrichment/preview-leads-from-supersearch",
        "method": "post",
        "headers": [
          {
            "name": "Authorization",
            "value": "Bearer {{connection.instantly}}"
          },
          {
            "name": "Content-Type",
            "value": "application/json"
          }
        ],
        "bodyType": "raw",
        "body": "{{toJSON(4.current_filters)}}"
      }
    }
  ]
}
```

---

## Maintenance & Monitoring

### 1. Set Up Monitoring

**Datadog/Monitoring Module:**
- Track execution time
- Monitor success rate
- Alert on failures

**What to Monitor:**
- API rate limits hit
- AI parsing failures
- Credit usage
- Lead count ranges

### 2. Regular Updates

**Weekly:**
- Review failed scenarios
- Check credit usage vs expectations
- Update AI prompts if needed

**Monthly:**
- Analyze lead quality
- Optimize filters based on conversions
- Update target count ranges

### 3. Cost Optimization

**Reduce Make Operations:**
- Combine HTTP calls where possible
- Use fewer AI calls (cache common queries)
- Batch process multiple searches

**Reduce Instantly Credits:**
- Start with minimal enrichment
- Add expensive enrichments only for qualified leads
- Use preview extensively before enriching

---

## Troubleshooting

### Issue: AI Returns Invalid JSON

**Solution:**
```
Add cleaning module:
1. Text Parser → Replace
   - Find: ```json, ```, `json
   - Replace: (empty)
2. Text Parser → Match Pattern
   - Pattern: \{.*\}
   - Extract first match
3. Then parse JSON
```

### Issue: Infinite Loop in Repeater

**Solution:**
```
Add max iteration hard stop:
- Router with filter: iteration >= 5
- Force set proceed_with_enrichment = true
```

### Issue: Rate Limiting from Instantly

**Solution:**
```
Add exponential backoff:
- Sleep module after each HTTP call
- Delay: {{multiply(attempt; 2)}} seconds
```

### Issue: Filters Not Refining

**Solution:**
```
Improve AI prompt specificity:
- Show previous counts
- Explain what worked/didn't
- Give concrete examples
- Limit to ONE change per iteration
```

---

## Next Steps

1. **Import the scenario** using the JSON blueprint
2. **Add your API connections**
3. **Test with webhook** using test payload
4. **Monitor first few runs** closely
5. **Iterate on AI prompts** based on results
6. **Add automation** (scheduling, approvals, etc.)

This setup will give you a fully automated AI agent that can intelligently find and enrich leads with minimal manual intervention!
