# Meridian — Attractor Spec Package

Complete specification for building Meridian using the [Attractor](https://github.com/strongdm/attractor) pipeline.

## Setup

Everything runs on one machine. One model serves both purposes:

```
Qwen3-Coder (UD-Q8_K_XL) on llama.cpp
├── Port 8085 ← Claude Code uses this to BUILD Meridian
└── Port 8085 ← Meridian's app code uses this to RUN intelligence features
```

No cloud APIs. No API keys.

## Contents

| File | What it is |
|---|---|
| `attractor-spec.md` | Pipeline graph (DOT), phases, data models, convergence criteria |
| `coding-agent-loop-spec.md` | Agent behavior: project conventions, test strategy, recovery |
| `unified-llm-spec.md` | Runtime LLM client (~60 lines, just an httpx wrapper for localhost:8085) |
| `scenarios/` | 20 scenario documents for LLM-as-judge validation |

## Scenarios

| # | Name | Phase |
|---|---|---|
| 01 | Register email/password | Auth |
| 02 | Google OAuth login | Auth |
| 03 | Token refresh/expiry | Auth |
| 04 | Task CRUD | Tasks |
| 05 | Cross-user isolation | Tasks |
| 06 | Search and pagination | Tasks |
| 07 | Daily plan creation | Planning |
| 08 | Reorder mid-day | Planning |
| 09 | Evening reflection | Planning |
| 10 | Timezone planning | Planning |
| 11 | Morning briefing | Notifications |
| 12 | Midday nudge | Notifications |
| 13 | Evening reflection prompt | Notifications |
| 14 | Notification preferences | Notifications |
| 15 | NL task capture | Intelligence |
| 16 | Pattern detection | Intelligence |
| 17 | AI task ordering | Intelligence |
| 18 | Full day lifecycle | Integration |
| 19 | Docker stack boot | Integration |
| 20 | iOS API compatibility | Integration |

## How to Use

### 1. Make sure llama.cpp is running

```bash
# Your existing setup — Qwen3-Coder on port 8085
curl http://localhost:8085/health  # should return 200
```

### 2. Feed to Claude Code

```bash
claude-code "Implement Meridian as described by the spec package in ./meridian-spec/"
```

Claude Code talks to your local Qwen3-Coder at :8085. The pipeline builds each phase, runs tests, and iterates.

### 3. Human Gates

You get prompted at three points:
- **Schema review** — approve DB design before code is written against it
- **Planning UX review** — approve the daily planning flow
- **Intelligence design review** — approve pattern detection and suggestion algorithms

### 4. Scenario Validation

Scenarios live outside the codebase (holdout set). After the pipeline builds each phase, a judge evaluates scenarios against the running software. Satisfaction is scored 0.0–1.0 per scenario. Pipeline converges at ≥ 0.85 aggregate.

### 5. Resource Contention

The coding agent and the app share the same model server. The pipeline handles this:
- **Coding phases:** Agent uses the model. App is not running.
- **Test phases:** Tests use a mock LLM client. Real model stays available for the agent.
- **After pipeline completes:** Run `LLM_INTEGRATION_TESTS=1 pytest` to test real LLM features.
