---
name: docker-container-optimizer
description: Design, write, and optimize Dockerfiles and container runtime setups efficiently and securely. Use this skill when Codex needs to create new containers, improve existing Dockerfiles, reduce image size and build times, increase security and reliability, or provide structured suggestions and technical brainstorming with alternatives and tradeoffs.
---

# Docker Container Optimizer

## Overview

Guide the design and implementation of Docker containers optimized for build speed, image size, security, observability, and production stability.
Provide both practical execution (ready-to-use Dockerfiles) and decision support (alternatives, risks, and priorities).

## Operational Workflow

1. Define goals and constraints before writing the Dockerfile.
Typical goals: fast startup, small image size, stronger security hardening, CI/CD compatibility, simple debugging.
Typical constraints: required base image, native dependencies, company policy requirements, target platforms (`linux/amd64`, `linux/arm64`).

2. Assess the current state.
If a Dockerfile exists, inspect it and identify bottlenecks in cache usage, layers, user privileges, dependency handling, and runtime signaling.
Use `scripts/dockerfile_audit.sh <path>` for a fast first-pass audit.

3. Propose a strategy with explicit tradeoffs.
Present 2-3 options when useful.
For each option, state: benefits, costs, impact on build time, impact on security, and impact on maintainability.

4. Implement the Dockerfile and operational notes.
Apply concrete optimizations:
- use multi-stage builds when separating build/runtime adds value;
- order layers to maximize cache hits;
- remove unnecessary packages and files;
- run as a non-root user;
- set `ENTRYPOINT`/`CMD` predictably;
- add `HEALTHCHECK` when the service requires it.

5. Validate the result.
Run at least minimum checks (`docker build`, runtime smoke test) whenever possible.
If validation is not possible in context, clearly state remaining limits and residual risks.

## Brainstorming Mode

When the task requires ideation or exploration, use a structured output in blocks:

1. Initial assumptions
2. Architectural options
3. Main risks
4. Recommended quick experiments
5. Recommended choice and rationale

Ask targeted questions only when blocking; when details are missing, choose reasonable defaults and declare them.

## Minimum Standards To Apply

- Prefer explicit image tags that can be updated in a controlled way.
- Avoid root processes when not required.
- Avoid `ADD` unless ADD-specific behavior is truly needed (tar auto-extract or URL with justification).
- Manage package manager caches to reduce unnecessary layers.
- Keep Dockerfiles readable, with short comments only where useful.

## Resources

- Technical playbook: `references/optimization-playbook.md`
- Brainstorming prompts and framework: `references/brainstorming-framework.md`
- Automated Dockerfile audit: `scripts/dockerfile_audit.sh`
