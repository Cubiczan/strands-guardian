# Tasks

## 1. Model resolution

- [x] 1.1 Add `resolve_model_id` with precedence (argument, then `STRANDS_MODEL_ID`, then `us.amazon.nova-pro-v1:0`) and reject ids containing `anthropic.` with an error that names the rejected id and the Nova Pro default. Verify with unit tests for default, blank env, CLI/env precedence, and each Anthropic shape (bare, `us.`, `global.`, ARN).
- [x] 1.2 Build the Strands agent with `BedrockModel(model_id=..., region_name="us-east-1")` and call the resolver from `main`, `run_guardian`, and `create_guardian_agent`, including mock mode. Verify a unit test that the constructed model id is `us.amazon.nova-pro-v1:0` and the region is `us-east-1`, and that an Anthropic id raises before a client call.

## 2. Operator-facing defaults

- [x] 2.1 Update README run instructions, the CLI epilog, `.env.example`, and the video-script lines that name Claude so the documented model is `us.amazon.nova-pro-v1:0`. Add a README IAM example that allows `bedrock:Converse` and `bedrock:ConverseStream` for the Nova Pro inference profile and does not name Anthropic. Verify by searching the tree that no default or example model id is `us.anthropic.claude-sonnet-4-20250514`.

## 3. Integration check

- [x] 3.1 Run the test suite and confirm it passes, including the existing tool tests and the new model tests.
