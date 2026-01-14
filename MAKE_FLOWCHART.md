```mermaid
flowchart TD
    Start([Webhook Trigger<br/>User submits goal]) --> Init[Initialize Variables<br/>iteration=1<br/>max_iterations=5<br/>proceed=false]
    
    Init --> AIGen[AI: Generate Initial Filters<br/>Claude analyzes goal<br/>Returns search filters]
    
    AIGen --> Clean[Clean AI Response<br/>Remove markdown<br/>Parse JSON]
    
    Clean --> Loop{Repeater Loop<br/>Max 5 iterations}
    
    Loop -->|Start iteration| Preview[HTTP: Preview Search<br/>POST /preview-leads<br/>Returns lead count]
    
    Preview --> AddCount[Add count to history<br/>Track iterations]
    
    AddCount --> Router{Route by Count}
    
    Router -->|count < min| TooFew[AI: Broaden Search<br/>Suggest filter changes<br/>to increase results]
    
    Router -->|count > max| TooMany[AI: Narrow Search<br/>Suggest filter changes<br/>to decrease results]
    
    Router -->|min ≤ count ≤ max| Perfect[Set proceed=true<br/>Optimal range found!]
    
    Router -->|iteration = max| MaxIter[Force proceed=true<br/>Max iterations reached]
    
    TooFew --> ParseRefine[Parse AI Refinement<br/>Update filters]
    TooMany --> ParseRefine
    
    ParseRefine --> IncIter[Increment iteration<br/>iteration++]
    
    IncIter --> Loop
    
    Perfect --> Done{Proceed?}
    MaxIter --> Done
    
    Done -->|auto_enrich=true| Enrich[HTTP: Enrich Leads<br/>POST /enrich-leads<br/>Create list]
    
    Done -->|auto_enrich=false| Approval[Send Approval Request<br/>Email or Slack<br/>Wait for response]
    
    Approval -->|Approved| Enrich
    Approval -->|Rejected| Cancel[Send Cancellation Notice]
    
    Enrich --> Status[HTTP: Get Status<br/>Check enrichment progress]
    
    Status --> Log[Optional: Log to Sheets<br/>Record search details]
    
    Log --> Notify[Send Success Notification<br/>Email/Slack with results]
    
    Notify --> End([Return Response<br/>Show final filters & count])
    
    Cancel --> End
    
    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style AIGen fill:#fff4e6
    style TooFew fill:#fff4e6
    style TooMany fill:#fff4e6
    style Preview fill:#f3e5f5
    style Enrich fill:#f3e5f5
    style Status fill:#f3e5f5
    style Perfect fill:#e8f5e9
    style Router fill:#fff9c4
    style Done fill:#fff9c4
    style Loop fill:#fff9c4
```

## How to Use This Diagram

### Module Mapping

1. **Blue (Start/End)** - Webhook modules
2. **Orange (AI)** - Anthropic Claude modules
3. **Purple (HTTP)** - Instantly.ai API calls
4. **Green (Success)** - Completion states
5. **Yellow (Decision)** - Routers and conditional logic

### Flow Explanation

#### Phase 1: Initialization (Top)
- Webhook receives user goal
- Variables initialized
- AI generates initial filters

#### Phase 2: Refinement Loop (Middle)
- Preview search → Get count
- Router checks if count is optimal
- If not optimal: AI suggests refinements
- Loop continues until optimal or max iterations

#### Phase 3: Enrichment (Bottom)
- If auto-enrich: Run immediately
- If manual: Wait for approval
- Execute enrichment
- Notify user of completion

### Key Decision Points

1. **Router (Count Check)**
   - Too Few → Broaden
   - Too Many → Narrow
   - Just Right → Proceed
   - Max Iterations → Force proceed

2. **Proceed Decision**
   - Auto-enrich enabled → Enrich immediately
   - Manual approval → Send notification & wait

### Iteration Example

```
Iteration 1: 50,000 leads → Too Many → Narrow to CO only
Iteration 2: 5,000 leads → Too Many → Add company size 10-500
Iteration 3: 1,200 leads → Perfect! → Proceed to enrich
```

## Variables Tracked

- `iteration` - Current loop count (1-5)
- `current_filters` - Active search filters (updated each iteration)
- `lead_counts` - Array of counts from each iteration
- `proceed` - Boolean flag to break loop
- `target_min` / `target_max` - Target lead count range

## Error Handling

Each major module should have error handlers:

- **HTTP Errors** → Retry with exponential backoff
- **AI Parse Errors** → Clean response and retry
- **Rate Limits** → Wait and retry
- **Max Iterations** → Proceed with warning

## Optimization Tips

1. **Reduce Iterations** - Start with better initial filters
2. **Cache Common Searches** - Store successful filters
3. **Use Haiku for Refinement** - Cheaper AI model
4. **Batch Preview Calls** - If searching multiple goals
