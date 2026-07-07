# Shopify/eCommerce AI Automation Research Report

Date: 2026-07-08

## Problem

Shopify merchants handle many repeatable operational events: order questions, damaged product requests, inventory dips, post-purchase marketing, and possible fraud. The proposed system automates triage and draft actions while keeping humans in control for customer-facing or financially sensitive decisions.

## Compared Tools

| Tool | Capabilities | Pricing Snapshot | Scalability | Integration | Limitations | Best Use Case |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI API | Strong general reasoning, structured output, tool calling, agents, embeddings, multimodal options | Official API pricing lists models per 1M tokens. Example standard prices include `gpt-5.4-mini` at $0.75 input and $4.50 output per 1M tokens, and `gpt-5.4-nano` at $0.20 input and $1.25 output per 1M tokens. | High, with batch/flex/priority tiers and caching | Excellent Python/JS SDKs and broad ecosystem | Vendor dependency, token cost management, model/version churn | Default production LLM for classification, summaries, structured JSON actions, and cost-efficient drafting |
| Google Gemini API | Large-context models, strong multimodal support, Google Search/Maps grounding, competitive Flash tier | Gemini 2.5 Flash standard pricing is listed at $0.30 input and $2.50 output per 1M tokens; Gemini 2.5 Pro is $1.25 input and $10 output per 1M tokens for prompts <= 200k tokens. | Strong for high-context product catalogs and multimodal product data | Good SDKs, Google Cloud integration, AI Studio testing | Model deprecations and grounding costs need monitoring | Product catalog enrichment, long-context merchandising analysis, multimodal product QA |
| Claude API | Strong long-context reasoning, agentic coding/review workflows, careful support tone | Claude Platform docs list Sonnet 5 introductory pricing through 2026-08-31 at $2 input and $10 output per MTok, then $3 input and $15 output per MTok from 2026-09-01. Haiku 4.5 is $1 input and $5 output per MTok. | Strong for complex support and policy-heavy workflows | API, AWS Bedrock, Google Cloud, Microsoft Foundry | Higher output cost, tokenization changes, model availability details require tracking | Escalated support drafts, nuanced policy decisions, complex order/risk reasoning |
| n8n | Low-code workflow builder, webhooks, queues, many SaaS integrations, AI workflow builder | n8n cloud Starter is 20 EUR/month annually for 2.5k executions; Pro is 50 EUR/month annually for 10k executions; Business is 667 EUR/month annually for 40k self-hosted executions. | Good for operations teams; Enterprise supports 200+ concurrent executions and external secret stores | Excellent for Shopify, Slack, email, Google Sheets, CRM, HTTP, GraphQL | Not a model by itself; complex branching can become hard to govern | Business workflow layer for approvals, Slack alerts, CRM updates, and non-engineer automation ownership |
| Sarvam AI | Indic-language chat, speech-to-text, text-to-speech, translation, document digitisation, voice agents, deployment flexibility | Sarvam lists Rs.1,000 free credits. Chat pricing shown includes Sarvam-105B at Rs.4 input, Rs.2.5 cached input, and Rs.16 output per 1M tokens; Sarvam-30B at Rs.2.5 input, Rs.1.5 cached input, and Rs.10 output per 1M tokens. | Strong India-focused option, with managed cloud, private cloud, on-prem, and enterprise deployment messaging | Python SDK, REST API, dashboard playground | Smaller ecosystem than OpenAI/Gemini/Claude; production fit depends on language mix and enterprise support needs | Indian-language customer support, voice commerce, WhatsApp/phone workflows, document processing |

## Shopify Platform Fit

Shopify webhooks are a good event trigger because they deliver near-real-time event data and avoid continuous polling. Production apps should verify webhook deliveries with HMAC and ignore duplicates using `X-Shopify-Webhook-Id`. Shopify's GraphQL Admin API uses calculated query-cost limits and a leaky-bucket model, so enrichment jobs should cache data, use queues, and retry with backoff.

## Selected POC Design

The prototype uses Python, local RAG, and deterministic offline AI. This was selected because the assignment can be reviewed without paid services, API keys, or network access. The design still maps cleanly to production LLM providers:

- Mock AI in the POC proves the orchestration contract.
- OpenAI or Gemini can replace the mock for low-cost classification and drafting.
- Claude can be routed only for complex cases.
- n8n can receive the structured action plan and handle approvals or SaaS updates.

## Estimated Infrastructure Cost

Small merchant estimate:

- FastAPI webhook service on a small VPS or serverless platform: $5 to $25/month.
- Postgres: $0 to $20/month for starter managed tiers.
- Queue: $0 to $15/month at low volume.
- n8n: self-hosted community edition on the same VPS for low cost, or n8n Starter at 20 EUR/month annually.
- LLM usage: often under $10 to $50/month for thousands of short classifications/drafts if using low-cost models and caching.

Mid-market estimate:

- App service plus worker autoscaling: $50 to $300/month.
- Managed Postgres and Redis/SQS/Cloud Tasks: $50 to $300/month.
- Vector database or pgvector: $25 to $300/month depending on corpus size.
- n8n Pro/Business or custom workflow UI: 50 EUR/month to 667 EUR/month annually.
- LLM usage: $100 to $1,000+/month depending on order volume, response length, and premium model routing.

## Risks And Limitations

- AI can draft incorrect refund, discount, or fraud decisions, so financial and customer-facing actions need approval thresholds.
- Shopify rate limits require caching, backoff, and asynchronous processing.
- Customer data must be minimized before sending to external AI providers.
- Provider pricing and model availability change, so production should centralize model routing config.
- RAG quality depends on clean policies and product knowledge. Old policies can produce bad recommendations.

## Production Scaling Plan

1. Start with AI-generated drafts and internal alerts only.
2. Add audit logs, human approvals, and confidence thresholds.
3. Add vector search over policies, product specs, return rules, and past resolved support tickets.
4. Route routine tasks to cheaper models and escalations to stronger models.
5. Add background workers for batch catalog enrichment and daily analytics.
6. Add n8n or Make for ops-owned actions such as Slack, email, CRM, and helpdesk updates.
7. Add evaluation sets for support replies, inventory alerts, false fraud positives, and cost per order.

## Sources

- OpenAI API pricing: https://platform.openai.com/docs/pricing
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Claude Platform pricing: https://docs.anthropic.com/en/docs/about-claude/pricing
- n8n pricing: https://n8n.io/pricing/
- Sarvam AI pricing: https://www.sarvam.ai/api-pricing
- Sarvam AI platform overview: https://www.sarvam.ai/
- Shopify webhooks: https://shopify.dev/docs/apps/build/webhooks
- Shopify API limits: https://shopify.dev/docs/api/usage/limits
