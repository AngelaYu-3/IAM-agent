# IAM-agent
Langflow implementation of an IAM agentic MVP workflow that takes an inputted log of user roles & access permissions then analyzes if there are permission anomalies.

### Key Features
- **Intelligent Tool Selection**: Adapts analysis depth based on context and urgency
- **Multi-Agent Architecture**: Specialized security and compliance agents
- **Memory Capabilities**: References previous analyses and organizational patterns
- **Regulatory Compliance**: Built-in SOX, RBAC, and data protection policy knowledge

### Table of Contents
* [Workflow Image](#workflow-image)
* [Workflow Breakdown](#workflow-breakdown)
* [Example Output](#example-output)
* [Future Testing Prompts](#future-testing-prompts)
___

## Workflow Image
![workflow image](/images/workflow.png)
___

## Workflow Breakdown

### data
- mock_access_data.csv: input mock data
- mock_access_data_risk.csv: mock data but with risk assessment to cross check workflow outputs

### tools
user lookup tool:
- purpose: basic user information retrieval
- function: searches CSV data for specified user
- returns: username, department, role, permissions, employment status, risk flags
- when used: always first step in any analysis

peer comparison tool:
- purpose: compare user permissions with peers in same role/department
- function: finds users with identical roles, calculates permission baselines
- returns: peer averages, permission deviations, unique permissions, outlier status
- when used: when user has unusual permission counts or patterns

risk pattern tool:
- purpose: analyze specific security risk patterns in permissions
- function: detects cross-dept access, destructive permissions, role mismatches
- returns: risk factors, severity scores, violation categories, overall risk level
- when used: when concerning permissions are identified

### memory
specific memory components such as AstraDB are overkill for such a MVP, thus used Langflow Agent Component's default Langflow tables.

### agents
security agent:
- role: technical security analysis
- tools: all 3 tools listed above
- output: security findings, tool usage reasoning, risk assessment

compliance agent:
- role: regulatory and policy expertise
- knowledge: embedded compliance policies (SOX, RBAC, etc.)
- output: policy violations, compliance risk, enhanced recommendations

### llms
formatting llm:
- role: clean up messy LLM output
- function: proper spacing and structure
- output: readable final reports

___

## Example Output
<img src="/images/output1.png" alt="output1 image" width="600">

___

## Future Testing Prompts

### Tool Selection Reasoning Tests

*Just need a quick status check on user001 - is everything normal?*
- user lookup tool only, maybe peer comparison
- "quick check" should trigger minimal investigation

*I'm very concerned about user016 - they're a contractor with suspicious access patterns*
- user lookup, risk pattern, compliance checker tools
- "very concerned", "contractor", "suspicious" should trigger comprehensive analysis

*We have a SOX audit tomorrow - verify user014's financial system compliance*
- user lookup, compliance checker tools
- "SOX audit" context should focus on compliance tools

### Memory / Cross Session Tests

*Analyze user017 for any security violations*
- initial analysis - creates memory
- full analysis, stores findings for future reference

*Check user017 again - have the issues I found before been fixed?*
- follow up analysis - uses memory
- references previous analysis, focuses on previously identified issues, compares current vs past state

*Investigate user025 - they're in a similar role to someone I asked about earlier*
- demonstrates learning
- references similar previous user (user017 or user014), applies learned patterns about role-based violations, shows organization intelligence

