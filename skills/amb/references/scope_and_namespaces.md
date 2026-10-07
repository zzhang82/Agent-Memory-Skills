# Scope and namespaces

Every read and write names one namespace. A namespace is a bucket, not a permission grant. Seeing `global` in a tool schema does not authorize writing operating rules there.

AMB v0.36.0 binds a git checkout to exactly one `project:<slug>` through project init. Resolution reads that binding. It does not create one.

## Repository-backed projects

From the checkout (or any path inside it):

```bash
agent-memory-bridge project resolve .
```

The command prints `project.resolution.v1` JSON and does not refresh repository WHAT or rebind the repo.

| `status` | Meaning | What to do |
|---|---|---|
| `bound` | Exactly one valid namespace | Use `namespace`. It matches `project:<slug>`. |
| `no_binding` | Git repo, no project namespace yet | Do not invent a slug. Route to `amb-connect` / `project init`. |
| `ambiguous_binding` | More than one namespace, an invalid name, or an unreadable binding file | Do not pick one. Report the ambiguity. |
| `not_a_repository` | Path is not a git work tree | Use a repository-free namespace only if the user named one. |
| `repository_unavailable` | Path or git could not be read | Stop. Do not fall back to the directory name. |

Exit code is 0 only for `bound`. Any other status exits non-zero.

Slug shape accepted by the resolver: `project:` plus a lowercase letter or digit, then up to 61 more `[a-z0-9-]`, ending in a letter or digit. Examples: `project:demo-app`. Not valid: `project:Demo`, `project:demo_app`.

These inputs do **not** choose identity, even if a caller sends them: `caller_tags`, `client_workspace`, `prompt_text`, `source_client`, `source_model`. Folder names do not choose it either.

A bound resolve can include `repository_identity` and `repository_what`. WHAT is derived repository context. Do not store it back as a decision. Memory remains WHY.

`project init` creates or confirms the binding. It is out of scope for this skill.

## Explicit namespaces

If the user names the scope, use that string and do not also run resolve to "fix" it.

| Form | Use |
|---|---|
| `project:<slug>` | One product or repo's durable decisions, gotchas, constraints, procedures. |
| `domain:<name>` | Practice shared across repos: release, retrieval, a library's gotchas. |
| `global` | Operating rules that are not about one repo. Rare. Prefer a named domain unless the user said global. |

`browse` takes `domain` as the plain name (`release`), while `namespace` for those notes is `domain:release`.

## Repository-free scopes

Bots, scratch work, and shared practices have no git binding. Do not call `project resolve` and then store under a guessed project.

- Shared engineering notes go to `domain:<name>`.
- A standing rule for how agents should behave, across repos, goes where the user said. Default proposal: a named domain, not `global`, until they ask for global.
- A one-off chat decision that the user did not ask to keep does not get a namespace. Do not store it.

When a later session is inside a bound checkout, recall `project:<slug>` first. Add `domain:<name>` only when the task matches that domain. Do not recall `global` as a substitute for a missing project binding.

## Write routing

| Record | Namespace |
|---|---|
| This repo's decision, gotcha, constraint, procedure | The bound `project:<slug>` |
| A confirmed cross-repo practice | `domain:<name>` |
| A handoff another worker must claim | The same project or domain the work belongs to, `kind="signal"` |
| A lesson inferred but not confirmed | Nowhere, until the user confirms |

One fact lives in one namespace. Do not mirror a project decision into `global` "so other agents see it."

## Redlines

- Never treat `no_binding` as permission to `store` under `project:` plus the folder name.
- Never resolve scope from the prompt, the client workspace label, or tags.
- Never write a shared domain note into a project namespace just because that checkout is open.
- Never use another project's namespace because recall there happened to return something useful.
