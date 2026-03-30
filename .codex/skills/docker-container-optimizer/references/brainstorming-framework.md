# Brainstorming Framework For Docker Decisions

Use this structure when the user asks for ideas, alternatives, or tradeoff analysis.

## 1. Problem Frame

State in one short paragraph:
- workload type (API, worker, batch, CLI)
- operational profile (high QPS, memory bound, sporadic jobs)
- hard constraints (security policy, image family, CI budget)

## 2. Candidate Options (2-3)

For each option include:
- summary of the approach
- expected gains
- expected costs
- key risks

## 3. Tradeoff Matrix

Score each option on:
- build speed
- runtime performance
- image size
- security posture
- maintainability

Use qualitative scores (`low`, `medium`, `high`) when hard data is unavailable.

## 4. Fast Experiments

Propose small experiments with measurable outputs:
- build time comparison
- final image size comparison
- startup latency smoke test
- memory usage under representative load

## 5. Recommendation

Provide:
- recommended option
- why it is preferred in this context
- fallback option if constraints change

## Prompt Starters

- "Propose 3 Dockerfile strategies for this service and compare tradeoffs."
- "Brainstorm how to shrink this image by 30% without harming reliability."
- "Give an optimization plan that improves CI build time first, then size."
- "List risky changes vs safe quick wins for this Dockerfile."
