# AGENT.md

## Mission
This repository uses an AI agent to accelerate safe delivery.

## Working mode
Use branch-based and pull-request-based changes.

## The agent may
- read the repository
- create branches
- edit code, tests, scripts, and docs
- open pull requests with notes

## The agent must not
- push directly to protected branches
- commit secrets
- remove security checks without approval
- claim tests ran when they did not

## Approval needed for
- auth changes
- secret handling changes
- webhook verification behavior
- deployment or infrastructure changes
- database schema changes
- public API breaking changes

## Safe autonomous work
- docs
- tests
- low-risk bug fixes
- CI fixes
- small UI polish
- low-risk refactors

## Validation order
1. targeted tests
2. full tests
3. smoke tests
4. manual file review

## Done means
- change implemented
- docs updated when needed
- validation notes included
- risks called out clearly
