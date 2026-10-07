# bedrock-llm Specification

## Purpose

Select the Amazon Bedrock model that reasons for Strands Guardian, defaulting to a credit-eligible Amazon Nova model and refusing Anthropic model ids.

## Requirements

### Requirement: Default to Amazon Nova Pro
When no model override is set, the agent SHALL call Amazon Bedrock in `us-east-1` with the Converse API and model id `us.amazon.nova-pro-v1:0`.

#### Scenario: No flag and no environment variable
- **WHEN** the operator starts the agent without `--model` and without `STRANDS_MODEL_ID`
- **THEN** the Bedrock request uses model id `us.amazon.nova-pro-v1:0` in region `us-east-1`

#### Scenario: Blank environment variable
- **WHEN** `STRANDS_MODEL_ID` is empty or whitespace and no model argument is passed
- **THEN** the agent uses `us.amazon.nova-pro-v1:0`

### Requirement: Non-Anthropic model override
The agent SHALL accept a non-Anthropic Bedrock model id from the `--model` flag or from `STRANDS_MODEL_ID`. An explicit model argument MUST take precedence over the environment variable.

#### Scenario: CLI flag
- **WHEN** the operator passes `--model us.amazon.nova-lite-v1:0`
- **THEN** the Bedrock request uses model id `us.amazon.nova-lite-v1:0`

#### Scenario: Environment variable
- **WHEN** `STRANDS_MODEL_ID` is `us.amazon.nova-lite-v1:0` and no model argument is passed
- **THEN** the Bedrock request uses model id `us.amazon.nova-lite-v1:0`

#### Scenario: Argument wins over environment
- **WHEN** `STRANDS_MODEL_ID` is `us.amazon.nova-lite-v1:0` and the model argument is `us.amazon.nova-micro-v1:0`
- **THEN** the Bedrock request uses model id `us.amazon.nova-micro-v1:0`

### Requirement: Reject Anthropic model ids
The agent MUST reject a model id whose provider is Anthropic before any Bedrock call, including mock mode. The error MUST include the rejected id and MUST identify `us.amazon.nova-pro-v1:0` as the supported default.

#### Scenario: Regional Anthropic inference profile
- **WHEN** the model id is `us.anthropic.claude-sonnet-4-20250514`
- **THEN** the agent fails with an error that includes that id and does not call Bedrock

#### Scenario: Bare Anthropic model id
- **WHEN** the model id is `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **THEN** the agent rejects that id with the same class of error

#### Scenario: Anthropic id from the environment
- **WHEN** `STRANDS_MODEL_ID` is `global.anthropic.claude-sonnet-4-20250514` and no model argument is passed
- **THEN** the agent rejects that id

#### Scenario: Anthropic foundation-model ARN
- **WHEN** the model id contains `/anthropic.`
- **THEN** the agent rejects that id

### Requirement: Operator docs use Nova Pro
README, CLI examples, and `.env.example` MUST present `us.amazon.nova-pro-v1:0` as the default Bedrock model and MUST NOT instruct the operator to pass an Anthropic model id.

#### Scenario: Documented default
- **WHEN** an operator reads the Bedrock run instructions, the CLI help examples, or `.env.example`
- **THEN** the shown model id is `us.amazon.nova-pro-v1:0` and no Anthropic model id is offered as the model to use

### Requirement: IAM example allows Nova Pro
The README MUST include an IAM policy example that allows Bedrock Converse for the `us.amazon.nova-pro-v1:0` inference profile in `us-east-1`. The example MUST NOT allow Anthropic models.

#### Scenario: Policy example contents
- **WHEN** an operator reads the IAM example in the README
- **THEN** it allows `bedrock:Converse` and `bedrock:ConverseStream` on `us.amazon.nova-pro-v1:0` and does not name an Anthropic model
