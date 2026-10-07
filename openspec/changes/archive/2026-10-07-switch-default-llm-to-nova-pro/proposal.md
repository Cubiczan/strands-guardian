# Proposal

## Why

The owner's AWS promotional credits do not cover Anthropic Claude on Amazon Bedrock. Claude is billed through AWS Marketplace and `InvokeModel` is IAM-denied on the account, so the current default model cannot run. Amazon Nova is credit-eligible and is the model this agent should use.

## What Changes

- **BREAKING**: The default Bedrock model changes from `us.anthropic.claude-sonnet-4-20250514` to Amazon Nova Pro `us.amazon.nova-pro-v1:0` in `us-east-1`, invoked through Strands `BedrockModel` (Bedrock Converse).
- `--model` and `STRANDS_MODEL_ID` remain overrides for any non-Anthropic Bedrock model id.
- Model ids whose provider segment is `anthropic` (including `anthropic.*` and regional forms such as `us.anthropic.*`) are rejected with a clear error that names Nova Pro as the replacement.
- README, CLI examples, `.env.example`, demo-script copy, and tests stop presenting Claude as the default. The README documents the IAM actions required to call Nova Pro via Converse. No IAM policy file exists in the repo today.

## Capabilities

### New Capabilities

- `bedrock-llm`: Choose the Amazon Bedrock model for the Strands Guardian agent, default to Amazon Nova Pro on `us-east-1`, and refuse Anthropic model ids.

### Modified Capabilities

## Impact

- `src/strands_guardian/agent.py` — model resolution, Anthropic rejection, and `BedrockModel` construction.
- `README.md`, `.env.example`, CLI epilog, and the video-script lines that name Claude as the reasoning engine.
- New tests for the default, overrides, and Anthropic rejection. Existing tool tests stay in place.
- Operators must grant Bedrock Converse permissions on the Nova Pro inference profile instead of an Anthropic foundation model. No new Python dependencies.
