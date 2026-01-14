# Quick Start: Instantly AI Agent in Make.com

## 🚀 5-Minute Setup

### Step 1: Import the Scenario (30 seconds)

1. Download `make_scenario_blueprint.json`
2. Go to Make.com → Scenarios
3. Click "Create new scenario"
4. Click ⋯ menu → Import Blueprint
5. Upload the JSON file
6. Click "Save"

### Step 2: Configure Connections (2 minutes)

#### A. Instantly.ai Connection

1. Click any HTTP module with Instantly API call
2. Connection → Add → HTTP
3. Authentication: Bearer Token
4. Token: `your_instantly_api_key_here`
5. Name it: "Instantly API"
6. Save

**Find your API key:**
- Go to: https://app.instantly.ai/app/settings/integrations
- Create new API key
- Copy and paste into Make

#### B. Anthropic Claude Connection

1. Click any Anthropic module
2. Connection → Add → Anthropic
3. API Key: `your_anthropic_api_key_here`
4. Save

**Find your API key:**
- Go to: https://console.anthropic.com/settings/keys
- Create new key
- Copy and paste into Make

### Step 3: Test the Webhook (2 minutes)

1. Click the Webhook (first module)
2. Click "Run once"
3. Copy the webhook URL
4. Test with curl:

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Find CEOs at tech companies in Colorado with 50-200 employees",
    "target_count_min": 500,
    "target_count_max": 2000,
    "auto_enrich": false
  }'
```

5. Watch the scenario execute!

### Step 4: Check Results (30 seconds)

The webhook will respond with:
```json
{
  "status": "success",
  "goal": "Find CEOs...",
  "iterations": 3,
  "final_count": 1247,
  "filters": {...},
  "estimated_credits": 1870,
  "message": "Search refinement complete..."
}
```

---

## 📋 Configuration Checklist

### Required Settings

- [ ] Instantly.ai API key configured
- [ ] Anthropic API key configured  
- [ ] Webhook URL saved
- [ ] Test run completed successfully

### Optional Enhancements

- [ ] Email notification module added
- [ ] Google Sheets logging added
- [ ] Slack notification added
- [ ] Auto-enrichment enabled
- [ ] Schedule trigger added

---

## 🎯 Key Modules to Customize

### Module 3: Initial Filter Generator

**Where:** Anthropic → Create Completion

**Customize:**
```
System Prompt: (You can add industry-specific filters)

Example additions:
- funding_amount: {min: 5000000}
- recent_news: true
- hiring_signals: true
```

### Module 7: Preview Search

**Where:** HTTP → Make a Request

**Customize:**
- URL: (should already be correct)
- Headers: Add your API key
- Body: (auto-configured)

### Module 9 & 10: Refinement AI

**Where:** Anthropic → Create Completion (in Router routes)

**Customize the narrowing strategy:**
```
Current: Generic narrowing
Your option: Industry-specific
  "For B2B SaaS, prioritize companies using Salesforce or HubSpot"
```

---

## 🔧 Common Customizations

### 1. Change Target Lead Count

Edit Module 2 (Basic Feeder):
```json
{
  "target_min": 1000,  // Change from 500
  "target_max": 5000   // Change from 2000
}
```

### 2. Adjust Iteration Limit

Edit Module 6 (Repeater):
```
Repeats: 3  // Change from 5 for faster runs
```

### 3. Add Industry Focus

Edit Module 3 system prompt:
```
Add after "Available filters:":

"Priority industries for this search:
- Technology (required)
- SaaS (preferred)
- Cloud Services (preferred)"
```

### 4. Enable Auto-Enrichment

Change webhook test payload:
```json
{
  "goal": "...",
  "auto_enrich": true  // Change to true
}
```

### 5. Add Email Notifications

**After Module 12 (Respond):**

1. Add Module: Email → Send an Email
2. To: your@email.com
3. Subject: `Instantly Search Complete - {{7.data.count}} leads`
4. Body:
```
Goal: {{1.goal}}
Final Count: {{7.data.count}}
Iterations: {{2.iteration}}

View filters:
{{formatJSON(5)}}
```

---

## 🔍 Testing Guide

### Test 1: Basic Flow

**Payload:**
```json
{
  "goal": "Find marketing directors in California",
  "target_count_min": 500,
  "target_count_max": 2000,
  "auto_enrich": false
}
```

**Expected:**
- 1-5 iterations
- Final count: 500-2000
- Success response

### Test 2: Too Broad Search

**Payload:**
```json
{
  "goal": "Find executives in United States",
  "target_count_min": 500,
  "target_count_max": 2000,
  "auto_enrich": false
}
```

**Expected:**
- Initial count: 100,000+
- AI narrows with specific filters
- Multiple iterations
- Final count: in range

### Test 3: Too Narrow Search

**Payload:**
```json
{
  "goal": "Find CTOs at AI companies in Boulder with 20-30 employees using TensorFlow",
  "target_count_min": 500,
  "target_count_max": 2000,
  "auto_enrich": false
}
```

**Expected:**
- Initial count: <100
- AI broadens search
- Relaxes some constraints
- Final count: in range or reaches max iterations

---

## 🐛 Troubleshooting

### Issue: "Invalid JSON from AI"

**Fix Module 4 (Text Parser):**
```
Pattern: ```json|```|`
Global: true
Text: {{3.output}}
```

Add after Module 4:
```
Module: Text Parser → Match Pattern
Pattern: \{.*\}
Flags: s (dot matches newline)
```

### Issue: "Instantly API 401 Unauthorized"

**Check:**
1. API key is correct
2. No extra spaces in Bearer token
3. Key has correct scopes: `supersearch_enrichments:all`

**Fix:**
```
Module 7 Headers:
Authorization: Bearer YOUR_KEY_NO_SPACES
Content-Type: application/json
```

### Issue: "Repeater not stopping"

**Check Module 6:**
```
Break Condition: {{2.proceed}}

If still looping, add Router after Module 8:
Route: iteration >= max_iterations
Action: Set proceed = true
```

### Issue: "Filters not refining well"

**Improve AI prompts in Modules 9 & 10:**

Add to system prompt:
```
Previous counts: {{join(2.lead_counts; ', ')}}
Current iteration: {{2.iteration}}

Focus on the ONE most impactful change:
- Iteration 1: Geographic scope
- Iteration 2: Job title specificity  
- Iteration 3: Company size
- Iteration 4+: Keywords/industries
```

---

## 📊 Monitoring & Optimization

### View Execution History

1. Scenarios → Your Scenario
2. History tab
3. Click any run to see:
   - Each module's input/output
   - Execution time
   - Data processed

### Optimize Performance

**Reduce execution time:**
- Use fewer AI calls (cache common searches)
- Reduce max iterations (3 instead of 5)
- Simplify AI prompts

**Reduce costs:**
- Use Claude Haiku for refinement (cheaper)
- Use GPT-4 only for initial generation
- Add early termination conditions

**Improve accuracy:**
- Add industry-specific examples to prompts
- Store successful searches in Data Store
- Use historical data to predict optimal filters

---

## 🚀 Advanced Features

### 1. Add Google Sheets Logging

**After Module 12:**

Module: Google Sheets → Add a Row

**Spreadsheet:** "Lead Searches"
**Values:**
```
Date: {{formatDate(now; 'YYYY-MM-DD HH:mm')}}
Goal: {{1.goal}}
Final Count: {{7.data.count}}
Iterations: {{2.iteration}}
Filters: {{formatJSON(5)}}
Credits: {{multiply(7.data.count; 1.5)}}
Status: Success
```

### 2. Add Slack Notifications

**After Module 12:**

Module: Slack → Send a Message

**Channel:** #leads
**Message:**
```
🎯 Lead Search Complete!

*Goal:* {{1.goal}}
*Results:* {{7.data.count}} leads found
*Iterations:* {{2.iteration}}
*Est. Cost:* ~${{divide(multiply(7.data.count; 1.5); 222)}}

<https://app.instantly.ai|View in Instantly →>
```

### 3. Add Data Store for History

**Before Module 3:**

Module: Data Store → Search Records

**Data Store:** "Search History"
**Filter:**
```
goal CONTAINS {{1.goal}}
AND timestamp > {{addDays(now; -30)}}
```

**Logic:**
- If found: Use those filters as starting point
- If not found: Generate new filters with AI

### 4. Add Approval Workflow

**After Module 8 (Router):**

Add new route: "Manual Approval"

**Modules:**
1. Slack → Send Message (with approval buttons)
2. Slack → Wait for Response
3. Router → Check Approval
4. If approved: Continue to enrichment

### 5. Schedule Daily Searches

**Replace Module 1 (Webhook) with:**

Module: Schedule → Every Day

**Time:** 9:00 AM

**Then add:**

Module: Data Store → Get Records

**Query:** Saved search goals

**Array Iterator:** Process each goal

---

## 💰 Cost Breakdown

### Make.com Operations

- Webhook: 1 op
- Claude calls: 2-10 ops (depends on iterations)
- HTTP calls: 2-10 ops
- Parsers/Routers: 5-15 ops

**Total per search:** ~20-40 operations

**Make Pro Plan:** 10,000 ops/month = 250-500 searches

### Instantly.ai Credits

- Preview: FREE ✓
- Email enrichment: 1.5 credits/lead
- Additional enrichments: 0.5 credits each

**Example:** 1,000 leads with email + verification
- Cost: ~1,500 credits
- USD: ~$6.75

### Anthropic API

- Claude Sonnet 4: $3 per 1M tokens
- Average search: ~5,000 tokens (2-5 AI calls)
- Cost per search: ~$0.015

**Monthly at 100 searches:** ~$1.50

---

## 📝 Next Steps

1. ✅ Import and test basic scenario
2. ✅ Customize for your industry
3. ✅ Add monitoring (email/Slack)
4. ✅ Set up scheduled runs
5. ✅ Optimize based on results

---

## 🆘 Support Resources

- **Make.com Docs:** https://www.make.com/en/help
- **Instantly API:** https://developer.instantly.ai
- **Anthropic API:** https://docs.anthropic.com
- **Community:** https://community.make.com

---

## 📚 Related Files

- `MAKE_AI_AGENT_GUIDE.md` - Full detailed guide
- `make_scenario_blueprint.json` - Importable scenario
- `instantly_workflow.py` - Python alternative
- `README.md` - Complete API documentation

Happy automating! 🚀
