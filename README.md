# Agent-Memory-Skills

> **Give any AI coding agent governed project memory across sessions, tools, and machines.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![AMB Compatibility: v0.36.0](https://img.shields.io/badge/AMB_Core-v0.36.0-green.svg)](https://github.com/zzhang82/Agent-Memory-Bridge)
[![Schema: v12](https://img.shields.io/badge/Schema-v12-orange.svg)](https://github.com/zzhang82/Agent-Memory-Bridge)
[![MCP Tools: 17](https://img.shields.io/badge/MCP_Tools-17-purple.svg)](https://modelcontextprotocol.io)

`Agent-Memory-Skills` is the official companion skill repository for [Agent Memory Bridge (AMB)](https://github.com/zzhang82/Agent-Memory-Bridge).

While AMB provides the durable authority (SQLite/WAL, FTS5 lexical recall, Streamable HTTP / stdio MCP server), **these skills give your LLM the exact procedural knowledge to connect, configure, and use memory effectively.**

---

## 🧭 Why Two Skills?

Connecting a host and using memory day-to-day have fundamentally different lifecycles and context footprints:

```text
                        ┌────────────────────────────────────────┐
                        │          User / Agent Prompt           │
                        └──────────────────┬─────────────────────┘
                                           │
                 ┌─────────────────────────┴────────────────────────┐
                 ▼                                                  ▼
     "Connect AMB to Codex / OpenCode"               "Remember this architectural decision"
     "Deploy remote Docker authority"                "Recall prior gotchas for this bug"
     "Configure tool allowlists / hooks"             "Revise outdated database constraint"
                 │                                                  │
                 ▼                                                  ▼
      ┌─────────────────────┐                            ┌─────────────────────┐
      │     amb-connect     │                            │         amb         │
      │  (Host Integration) │                            │  (Everyday Memory)  │
      └──────────┬──────────┘                            └──────────┬──────────┘
                 │                                                  │
                 ▼                                                  ▼
      • Discovers host capabilities                      • Resolves bound project scope
      • Connects stdio or HTTP MCP                       • Contextual recall (<= 5 results)
      • Sets 6-tool Everyday profile                     • Checks live code vs memory WHY
      • Wires lifecycle hooks (optional)                 • Stores confirmed decisions
      • Proves 2-session First Win                       • Revises/annotates existing rows
```

| Skill | Primary Job | Typical Triggers |
|---|---|---|
| [`skills/amb`](skills/amb/) | **Everyday Memory** | "Remember that we use WAL mode", "What did we decide about auth?", "That database rule changed; update it." |
| [`skills/amb-connect`](skills/amb-connect/) | **Connection & Integration** | "Connect AMB to OpenCode", "Set up remote HTTP memory on our server", "Why is AMB reporting missing tools?" |

---

## 🛠️ The 17 MCP Tools & Everyday Profile

AMB exposes exactly **17 public MCP tools** backed by schema v12. Rather than overwhelming models with 17 simultaneous tool schemas, `Agent-Memory-Skills` establishes a recommended **6-tool Everyday Profile** for standard coding sessions:

| Profile | Tools Included | When to Use |
|---|---|---|
| **Everyday Memory** *(Recommended)* | `recall`, `browse`, `stats`, `store`, `revise`, `annotate` | Standard coding, bugfixes, architectural decisions, and memory maintenance. |
| **Retrieval Feedback** *(Optional)* | `feedback` | Explicit retrieval evaluation using 15-minute signed recall receipts. |
| **Maintenance** *(Operator)* | `forget`, `promote`, `export` | Explicit record deletion, record promotion, or portable namespace snapshot. |
| **Tracked Work** *(Advanced)* | `begin_run`, `record_run_event`, `get_run`, `complete_run` | Governed execution runs with server-minted verification receipts. |
| **Coordination Signals** *(Advanced)* | `claim_signal`, `extend_signal_lease`, `ack_signal` | Multi-agent handoffs, claim leases, and task polling. |

---

## 🚀 Quickstart

### 1. Connecting AMB to Your Agent Host (`amb-connect`)

Load `amb-connect` when setting up a new agent host or server:

```text
user> Connect AMB to my coding environment.
agent> [Loads amb-connect]
       1. Discovers host capabilities (stdio subprocess vs HTTP MCP).
       2. Connects to existing AMB or provisions new instance.
       3. Recommends the 6-tool Everyday Profile.
       4. Verifies via server doctor and the Two-Session First Win round trip.
```

### 2. Using Memory Day-to-Day (`amb`)

Once connected, load `amb` during coding sessions:

```text
user> Remember that we only merge pull requests after CI passes, because broken main blocked releases twice this week.
agent> [Loads amb]
       Stores explicit decision under bound project namespace with claim, reason, and scope.

--- [Fresh session later] ---

user> What is required before we merge a PR?
agent> [Loads amb]
       Recalls stored decision: CI must pass before merging.
```

---

## 🛡️ Memory Hygiene: Structure Over Prose

> *If an agent makes the same mistake twice, harden the repository environment—do not write more text to memory.*

A common failure mode is treating memory as a prompt trash can for linter warnings or syntax reminders. Mechanical rules belong in deterministic AST tools (linters, static type narrowing, pre-commit checks) at zero runtime token cost.

Before storing any memory record, apply the **3-Question Ingestion Filter**:
1. **Can a linter catch it?** Configure ESLint, Biome, or Ruff. Do *not* store in AMB.
2. **Can static types or runtime assertions enforce it?** Harden TypeScript types or Pydantic models. Do *not* store in AMB.
3. **Is it an irreversible architectural decision, domain boundary, or external SDK gotcha?** Store in AMB with explicit triggers and rationale.

---

## 🌐 Broad Host Compatibility

AMB runs over standard MCP. It connects to compatible agent runtimes capable of running MCP stdio or Streamable HTTP meeting its authentication requirements:

- **Local IDEs & CLIs**: OpenCode, Codex CLI, Claude Desktop, Cursor, Cline, Windsurf.
- **Server Bots & Custom Agents**: Grok bots, Discord/Slack agents, Dots, custom Python/Node scripts.
- **Remote / NAS Authorities**: Dockerized AMB serving Streamable HTTP at `/mcp` behind bearer token authentication.

---

## 📂 Repository Layout

```text
Agent-Memory-Skills/
├── skills/
│   ├── amb/                          # Everyday memory skill
│   │   ├── SKILL.md                  # Core skill entrypoint & 5-step loop
│   │   └── references/
│   │       ├── everyday_workflows.md # Step-by-step memory patterns
│   │       ├── record_templates.md   # Canonical decision, gotcha, constraint templates
│   │       ├── revision_and_correction.md # revise vs annotate vs forget
│   │       ├── scope_and_namespaces.md   # project:<slug> vs domain:<name>
│   │       ├── tool_matrix.md        # Complete 17-tool contract breakdown
│   │       └── advanced_modes.md     # Runs ledger and coordination signals
│   │
│   └── amb-connect/                  # Host connection & transport skill
│       ├── SKILL.md                  # 5-stage connection protocol
│       └── references/
│           ├── capability_discovery.md # Detecting host capabilities
│           ├── transports_and_auth.md  # stdio vs HTTP bearer auth
│           ├── local_stdio_recipe.md   # Setting up local stdio MCP
│           ├── remote_http_recipe.md   # Connecting to remote HTTP MCP
│           ├── docker_deployment.md    # Official Docker Compose deployment
│           ├── tool_profiles.md        # Everyday (6) vs Full (17) filtering
│           ├── lifecycle_and_hooks.md  # Generic lifecycle-hook automation
│           └── verification_and_repair.md # Doctor, verify, and first-win test
│
├── scripts/
│   └── validate_skills.py           # Integrity, link, and contract validator
├── tests/
│   ├── test_skills_structure.py     # Structural test suite
│   └── test_contracts.py            # Technical contract test suite
└── .github/workflows/
    └── ci.yml                       # Automated GitHub Actions test runner
```

---

## 🧪 Validation & Testing

Run the included test and validation suites:

```bash
# Validate skill markdown, frontmatter, references, and tool matrix
python3 scripts/validate_skills.py

# Run unit tests
python3 -m unittest discover -s tests
```

---

## 📜 License

MIT License. See [LICENSE](LICENSE).
