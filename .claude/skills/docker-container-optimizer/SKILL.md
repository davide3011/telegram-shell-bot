---
name: docker-container-optimizer
description: Design, write, and optimize Dockerfiles and container runtime setups efficiently and securely. Use this skill whenever the user wants to create a new container, improve an existing Dockerfile, reduce image size or build times, harden security, analyze docker-compose setups, or needs structured suggestions and technical brainstorming with alternatives and tradeoffs. Trigger even when the user just says "check my Dockerfile", "make this smaller", "harden this container", or "is my Docker setup ok".
---

# Docker Container Optimizer

Guide the design and implementation of Docker containers optimized for build speed, image size, security, observability, and production stability. Provide both practical output (ready-to-use Dockerfiles) and decision support (alternatives, risks, tradeoffs).

## Workflow

### 1. Define goals and constraints

Before writing or modifying anything, clarify:
- **Goals**: fast startup, small image, security hardening, CI/CD compatibility, multi-arch support
- **Constraints**: required base image, native deps, company policy, target platforms (`linux/amd64`, `linux/arm64`)

When a Dockerfile already exists, run the audit script first:
```bash
bash scripts/dockerfile_audit.sh <path-to-Dockerfile>
```
Use the output as the starting point for the analysis.

### 2. Assess current state

If a Dockerfile is provided, identify:
- cache layer ordering issues
- unnecessary packages or files
- missing `.dockerignore`
- privilege escalation (root user)
- apt/pip cache not cleared
- missing `HEALTHCHECK` for long-lived services
- multi-stage build opportunities

### 3. Propose a strategy with explicit tradeoffs

Present 2–3 options when multiple valid approaches exist. For each, state:
- benefits
- costs
- impact on build time, image size, security, and maintainability

Use `references/brainstorming-framework.md` when the task is exploratory or when the user asks for ideas, alternatives, or a comparison.

### 4. Implement

Apply concrete optimizations:
- use multi-stage builds when separating build/runtime reduces size meaningfully
- order layers to maximize cache hits (deps before source)
- remove package manager caches in the same `RUN` layer
- run as a non-root `USER`
- set `ENTRYPOINT`/`CMD` explicitly and predictably
- add `HEALTHCHECK` for long-lived services

Refer to `references/optimization-playbook.md` for detailed guidance on base image selection, layer strategy, multi-stage decisions, and security baseline.

### 5. Validate

Run `docker build` (and a smoke test if possible) to confirm the result. If validation is not feasible in context, state what remains to be verified and why.

## Minimum Standards

- Pin explicit image tags — avoid `:latest`
- Avoid root processes unless strictly required
- Prefer `COPY` over `ADD` unless ADD-specific behavior is needed
- Clear package manager caches within the same layer
- Keep Dockerfiles readable; add comments only where logic is non-obvious

## Resources

- `references/optimization-playbook.md` — prioritization, base image strategy, layer caching, multi-stage decisions, security baseline, review checklist
- `references/brainstorming-framework.md` — structured format for tradeoff analysis and option comparison
- `scripts/dockerfile_audit.sh <path>` — fast heuristic audit of an existing Dockerfile
