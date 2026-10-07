# Design

## Context

See proposal.md for why Claude cannot stay the default. Today `create_guardian_agent` passes a model-id string to `Agent(model=...)`. The fallback string is `us.anthropic.claude-sonnet-4-20250514`. Strands treats a bare string as a Bedrock model id and, when no id is passed, its own default is a Claude inference profile (often resolved in `us-west-2`). There is no IAM policy in the repo. README, `.env.example`, the CLI epilog, and two video scripts name Claude as the reasoning engine.

## Goals / Non-Goals

**Goals:**

- Resolve the model id in one place and construct a Strands `BedrockModel` pinned to `us-east-1`, which calls Bedrock Converse.
- Keep `--model` and `STRANDS_MODEL_ID` as overrides, with the argument winning.
- Reject Anthropic provider ids before a client call, including mock mode.
- Make the default, the rejection, and the docs testable without AWS credentials.

**Non-Goals:**

- A region flag or multi-region Nova routing (`eu.` / `apac.` profiles).
- Changing tool implementations, dossier scoring, or mock-pipeline behavior.
- Calling Bedrock from tests or enabling live Nova invocations in CI.

## Decisions

### Construct `BedrockModel` instead of passing a string

`Agent(model="us.amazon.nova-pro-v1:0")` would change the id but would not pin the client region. `BedrockModel` defaults the region to the session, then `AWS_REGION`, then `us-west-2`. The US Nova Pro inference profile is invoked from `us-east-1`.

```python
BedrockModel(model_id=resolved_id, region_name="us-east-1")
```

`BedrockModel` formats a Converse request (`modelId`, `messages`, `inferenceConfig`). That is the Converse path this change requires. Alternative considered: call `bedrock-runtime.converse` directly and drop Strands' model class. Rejected because the agent loop, tool config, and streaming already live in `BedrockModel`.

### One resolver, three call sites

`resolve_model_id(model_id)` applies precedence and the Anthropic check:

1. Explicit argument (`--model` or the `model_id` parameter), when non-blank.
2. `STRANDS_MODEL_ID`, when non-blank.
3. `us.amazon.nova-pro-v1:0`.

`main`, `run_guardian`, and `create_guardian_agent` all call it. Mock mode never builds a client, but it still resolves the id so a Claude override fails closed. `create_guardian_agent` resolves before the Strands-installed check so the rejection does not depend on the SDK import.

### Anthropic match

Treat a model id as Anthropic when the lowercased id contains `anthropic.`. That covers `anthropic.*`, `us.anthropic.*`, `global.anthropic.*`, and foundation-model ARNs that embed `/anthropic.`. Case is ignored. A dedicated exception subclass of `ValueError` carries the message. The CLI prints it via `ArgumentParser.error` (exit code 2). The message includes the rejected id and `us.amazon.nova-pro-v1:0`.

Alternative considered: reject any id containing `claude`. Rejected because the request is specifically `anthropic.*` provider ids, and a substring ban would be broader than the spec.

### Docs and IAM

README run instructions, the CLI epilog, `.env.example`, the architecture blurb, and the two video scripts replace Claude with Amazon Nova Pro. The README gains a minimal IAM example:

- Actions: `bedrock:Converse`, `bedrock:ConverseStream` (and the InvokeModel pair Strands uses when streaming falls back).
- Resources: the inference profile `us.amazon.nova-pro-v1:0` and the underlying `amazon.nova-pro-v1:0` foundation model in the US regions that profile can route to.
- No `anthropic.*` resource.

No policy file is added; none exists today.

### Tests

Unit tests cover resolver precedence, each Anthropic shape, and `create_guardian_agent` constructing `BedrockModel` with the Nova Pro id and `region_name="us-east-1"`. The Bedrock client is mocked so construction does not need credentials. A source/docs scan asserts the default string is Nova Pro and that `us.anthropic` is not a configured default. Existing haversine and priority tests stay unchanged.

## Risks / Trade-offs

- [Nova Pro tool-calling differs from Claude] → Live agent behavior is not re-tuned here. Mock mode, which CI runs, does not call the model. Operators validate live tool use with their own credentials.
- [`BedrockModel()` builds a boto3 client at init] → Tests patch the class. Production still needs AWS credentials only for non-mock runs, unchanged from today.
- [Cross-region inference needs both profile and foundation-model ARNs] → The README example lists both. A profile-only policy can still fail at invoke time; the snippet is the mitigation.
- [Hard-pinned `us-east-1`] → Operators in another partition cannot retarget the client without a code change. Acceptable: the requested default is the US profile in `us-east-1`.

## Migration Plan

1. Deploy the change. New installs default to Nova Pro.
2. If `STRANDS_MODEL_ID` is an Anthropic id, the process fails with the rejection error until the variable is changed or removed.
3. Replace any Claude Bedrock IAM statement with the Nova Pro example.
4. Rollback is a revert of this change. Re-enabling Claude also requires Marketplace billing and IAM that this account does not have.

## Open Questions

None. Region stays pinned to `us-east-1`; a later change can add a region override if an operator needs it.
