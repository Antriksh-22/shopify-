# Demo Walkthrough

## Goal

Demonstrate a Shopify/eCommerce automation workflow without any external API key.

## Scenario

A repeat VIP customer places an order and notes that a previous mug arrived damaged. The order also reduces mug inventory below its reorder point.

## Run

```bash
python -m shopify_ai_automation.cli
```

## Expected Actions

- Draft a support reply that references refund/replacement policy.
- Create inventory reorder alerts for low-stock SKUs.
- Create a post-purchase retention offer for the repeat VIP customer.

## Why This Counts As AI Automation

The POC uses a local RAG index to retrieve policy context, then runs specialist agents that simulate the structured decisions a production LLM workflow would return. The mock AI engine is deterministic so reviewers can run tests without secrets, billing, or network access.

## Production Upgrade Path

Replace `MockAIEngine` with an OpenAI, Gemini, Claude, or Sarvam adapter, keep the same `complete_json` contract, and add provider routing by action type and confidence threshold.
