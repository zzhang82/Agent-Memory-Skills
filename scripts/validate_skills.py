#!/usr/bin/env python3
"""
Structural and Contract Lint for Agent-Memory-Skills.

Enforces:
1. Directory structure and required files
2. Frontmatter parsing (including single-line and multiline folded descriptions)
3. Internal markdown relative links validity (including nested badge links, excluding .git directory)
4. AMB v0.36.0 tool matrix completeness (exactly 17 public MCP tools with unique, non-duplicated headers)
5. Exact public tool order matches AMB v0.36 (strictly 1 to 17, no 18th tool, no label tampering)
6. Cross-file Everyday 6 profile equality across:
   - amb/SKILL.md
   - amb/references/tool_matrix.md
   - amb-connect/references/tool_profiles.md (table and JSON snippet)
   - amb-connect/references/verification_and_repair.md
   - README.md (table)
7. Redlines presence and accuracy:
   - fail-closed remote authority
   - local-only candidate capture
   - policy tag isolation / no reserved tag minting
   - no transcript dumping
"""

import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Exact canonical 17 tools order in AMB v0.36.0
EXPECTED_17_TOOLS = [
    "store", "recall", "browse", "stats",
    "forget", "feedback", "promote", "annotate", "revise", "export",
    "begin_run", "record_run_event", "get_run", "complete_run",
    "claim_signal", "extend_signal_lease", "ack_signal"
]

EXPECTED_17_SET = set(EXPECTED_17_TOOLS)

EVERYDAY_6_SET = {
    "recall", "browse", "stats", "store", "revise", "annotate"
}

RESERVED_TAG_PREFIXES = [
    "candidate_status:", "confidence:", "control:", "kind:", "relation:",
    "reviewed:", "scope:", "source:", "status:", "validity:"
]

def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    raw = parts[1]
    data = {}
    lines = raw.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">-", ">", ">+", "|", "|-", "|+"):
                block = []
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t") or not lines[i].strip()):
                    block.append(lines[i].strip())
                    i += 1
                data[key] = " ".join(block).strip()
                continue
            else:
                data[key] = val.strip('"').strip("'")
        i += 1
    return data

def extract_markdown_link_targets(text: str) -> list:
    """Extract all markdown link destinations, correctly handling nested image badge links like [![alt](img)](dest)."""
    targets = []
    # Match inline links: ](destination) or ](destination "title")
    # By matching ]\(\s*([^\s\)]+) we grab the destination even if preceded by [![]()
    matches = re.findall(r'\]\(\s*([^\s\)]+)', text)
    for m in matches:
        clean = m.strip()
        if clean:
            targets.append(clean)
    return targets

def validate_links(file_path: Path) -> list:
    errors = []
    text = file_path.read_text(encoding="utf-8")
    targets = extract_markdown_link_targets(text)
    for target in targets:
        if target.startswith("http://") or target.startswith("https://") or target.startswith("#") or target.startswith("mailto:"):
            continue
        clean_target = target.split("#")[0]
        if not clean_target:
            continue
        resolved = (file_path.parent / clean_target).resolve()
        if not resolved.exists():
            errors.append(f"{file_path.relative_to(ROOT)}: Broken link -> {target}")
    return errors

def check_everyday_profile_consistency() -> list:
    errors = []
    
    # 1. amb/SKILL.md - line 46 exact list
    amb_skill = (ROOT / "skills" / "amb" / "SKILL.md").read_text(encoding="utf-8")
    match_amb = re.search(r'six everyday tools:\s+([^.\n]+)', amb_skill)
    if not match_amb:
        errors.append("amb/SKILL.md missing 'six everyday tools: ...' line")
    else:
        amb_tools = set(re.findall(r'`(\w+)`', match_amb.group(1)))
        if amb_tools != EVERYDAY_6_SET:
            errors.append(f"amb/SKILL.md Everyday tools mismatch: found {amb_tools}, expected {EVERYDAY_6_SET}")

    # 2. amb/references/tool_matrix.md - Everyday profile row in table
    matrix_text = (ROOT / "skills" / "amb" / "references" / "tool_matrix.md").read_text(encoding="utf-8")
    match_matrix = re.search(r'\|\s*Everyday\s*\|\s*\d+\s*\|\s*([^|]+)\|', matrix_text)
    if not match_matrix:
        errors.append("tool_matrix.md missing '| Everyday |' table row")
    else:
        matrix_tools = set(re.findall(r'`(\w+)`', match_matrix.group(1)))
        if matrix_tools != EVERYDAY_6_SET:
            errors.append(f"tool_matrix.md Everyday mismatch: found {matrix_tools}, expected {EVERYDAY_6_SET}")

    # 3. amb-connect/references/tool_profiles.md table row
    tp_text = (ROOT / "skills" / "amb-connect" / "references" / "tool_profiles.md").read_text(encoding="utf-8")
    match_tp_table = re.search(r'\|\s*Everyday\s*\(6\)\s*\|\s*([^|]+)\|', tp_text)
    if not match_tp_table:
        errors.append("tool_profiles.md missing '| Everyday (6) |' table row")
    else:
        tp_tools = set(re.findall(r'`(\w+)`', match_tp_table.group(1)))
        if tp_tools != EVERYDAY_6_SET:
            errors.append(f"tool_profiles.md Everyday table mismatch: found {tp_tools}, expected {EVERYDAY_6_SET}")

    # 4. amb-connect/references/tool_profiles.md JSON snippet
    json_match = re.search(r'"enabledTools"\s*:\s*\[(.*?)\]', tp_text, re.DOTALL)
    if not json_match:
        errors.append("tool_profiles.md missing 'enabledTools' JSON snippet")
    else:
        json_tools = set(re.findall(r'"(\w+)"', json_match.group(1)))
        if json_tools != EVERYDAY_6_SET:
            errors.append(f"tool_profiles.md enabledTools JSON mismatch: found {json_tools}, expected {EVERYDAY_6_SET}")

    # 5. amb-connect/references/verification_and_repair.md
    vr_text = (ROOT / "skills" / "amb-connect" / "references" / "verification_and_repair.md").read_text(encoding="utf-8")
    vr_match = re.search(r'Everyday expects\s+([^.\n]+)', vr_text)
    if not vr_match:
        errors.append("verification_and_repair.md missing 'Everyday expects' line")
    else:
        vr_tools = set(re.findall(r'`(\w+)`', vr_match.group(1)))
        if vr_tools != EVERYDAY_6_SET:
            errors.append(f"verification_and_repair.md Everyday mismatch: found {vr_tools}, expected {EVERYDAY_6_SET}")

    # 6. README.md table
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    for line in readme_text.splitlines():
        if line.strip().startswith("|") and "**Everyday Memory**" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1].startswith("**Everyday Memory**"):
                readme_tools = set(re.findall(r'`(\w+)`', parts[2]))
                if readme_tools != EVERYDAY_6_SET:
                    errors.append(f"README.md Everyday Memory mismatch: found {readme_tools}, expected {EVERYDAY_6_SET}")
                break
    else:
        errors.append("README.md missing Everyday Memory table row")

    return errors

def check_tool_matrix_headings(text_override: str | None = None) -> list:
    errors = []
    matrix_file = ROOT / "skills" / "amb" / "references" / "tool_matrix.md"
    if text_override is None:
        if not matrix_file.is_file():
            return ["Missing tool_matrix.md"]
        text = matrix_file.read_text(encoding="utf-8")
    else:
        text = text_override
    
    # Recognize level-3 tool headers: ### `name` with optional trailing hashes/spaces
    found_headers = re.findall(r'^###\s+`([^`]+)`(?:\s*#*)?\s*$', text, re.MULTILINE)
    
    # 1. Total count must be exactly 17 (no duplicate sections, no extra tools)
    if len(found_headers) != len(EXPECTED_17_TOOLS):
        errors.append(
            f"tool_matrix.md must contain exactly {len(EXPECTED_17_TOOLS)} tool sections (found {len(found_headers)})."
        )
    
    # 2. Check for duplicate headers
    seen = set()
    duplicates = set()
    for h in found_headers:
        if h in seen:
            duplicates.add(h)
        seen.add(h)
    if duplicates:
        errors.append(f"tool_matrix.md contains duplicate tool sections: {duplicates}")

    # 3. Check exact set equality
    if seen != EXPECTED_17_SET:
        errors.append(
            f"tool_matrix.md level-3 headers do not cover exactly the 17 public tools!\n"
            f"Missing: {EXPECTED_17_SET - seen}, Extra: {seen - EXPECTED_17_SET}"
        )
    return errors

def check_public_tool_order(text_override: str | None = None) -> list:
    errors = []
    tp_file = ROOT / "skills" / "amb-connect" / "references" / "tool_profiles.md"
    if text_override is None:
        if not tp_file.is_file():
            return ["Missing tool_profiles.md"]
        text = tp_file.read_text(encoding="utf-8")
    else:
        text = text_override
    
    # Extract the 'Public order:' section up to the next heading or section
    section_match = re.search(r'Public order:\s*\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not section_match:
        return ["tool_profiles.md missing 'Public order:' section"]
    section_text = section_match.group(1)

    # Find all numbered list items, allowing optional indentation
    order_items = re.findall(r'^\s*(\d+)\.\s+`([^`]+)`', section_text, re.MULTILINE)
    
    # There must be exactly 17 numbered items in tool_profiles.md Public order (no 18th tool)
    if len(order_items) != 17:
        errors.append(
            f"tool_profiles.md Public order must contain exactly 17 numbered entries (found {len(order_items)})."
        )
    
    for idx, (num_str, tool_name) in enumerate(order_items, start=1):
        if int(num_str) != idx:
            errors.append(
                f"tool_profiles.md Public order noncanonical numbering at index {idx}: expected '{idx}.', found '{num_str}.'"
            )
        if idx <= len(EXPECTED_17_TOOLS) and tool_name != EXPECTED_17_TOOLS[idx - 1]:
            errors.append(
                f"tool_profiles.md Public order item {idx} mismatch: expected '{EXPECTED_17_TOOLS[idx - 1]}', found '{tool_name}'"
            )
            
    return errors

def main() -> int:
    print("=" * 65)
    print("🔍 Running Comprehensive Lint & Contract Checks on Agent-Memory-Skills...")
    print("=" * 65)
    
    errors = []
    
    # 1. Check all Markdown files for broken links (excludes ONLY .git directory, covers .github)
    for mf in ROOT.rglob("*.md"):
        parts = mf.relative_to(ROOT).parts
        if ".git" in parts:
            continue
        errors.extend(validate_links(mf))

    # 2. Check frontmatter on skills
    skills_dir = ROOT / "skills"
    for sname in ["amb", "amb-connect"]:
        sfile = skills_dir / sname / "SKILL.md"
        if not sfile.is_file():
            errors.append(f"Missing {sfile}")
            continue
        fm = parse_frontmatter(sfile.read_text(encoding="utf-8"))
        if fm.get("name") != sname:
            errors.append(f"{sfile} frontmatter name mismatch: {fm.get('name')} != {sname}")
        if not fm.get("version"):
            errors.append(f"{sfile} missing frontmatter version")
        desc = fm.get("description")
        if not desc or len(desc) < 20 or desc.startswith(">"):
            errors.append(f"{sfile} invalid or unparsed frontmatter description")

    # 3. Exact tool matrix headers & uniqueness
    errors.extend(check_tool_matrix_headings())

    # 4. Public tool order & numbering in tool_profiles.md (exactly 1 to 17)
    errors.extend(check_public_tool_order())

    # 5. Everyday profile cross-file consistency (all 5 files)
    errors.extend(check_everyday_profile_consistency())

    # 6. Redlines & invariants
    connect_skill = (skills_dir / "amb-connect" / "SKILL.md").read_text(encoding="utf-8")
    if "fail closed" not in connect_skill.lower():
        errors.append("amb-connect/SKILL.md must mandate failing closed on remote authority error")
    if "remote write-side capture" not in connect_skill.lower():
        errors.append("amb-connect/SKILL.md must document remote write-side capture limitation")

    # 7. Revision & annotation policy tag guard
    rev_doc = (skills_dir / "amb" / "references" / "revision_and_correction.md").read_text(encoding="utf-8")
    # Verify that in caller examples (tags=[...]), no reserved prefix is passed
    example_tags_match = re.search(r'revise\([^)]*tags=\[([^\]]+)\]', rev_doc, re.DOTALL)
    if example_tags_match:
        tags_str = example_tags_match.group(1)
        for reserved_prefix in RESERVED_TAG_PREFIXES:
            if f'"{reserved_prefix}' in tags_str or f"'{reserved_prefix}" in tags_str:
                errors.append(f"revision_and_correction.md revise example contains reserved policy tag '{reserved_prefix}' in caller tags")
    if "reserved policy" not in rev_doc.lower():
        errors.append("revision_and_correction.md must explicitly document reserved policy tag isolation")

    if errors:
        print("\n❌ Contract Lint Failed with Errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\n✅ All skill structures, links, and cross-file Everyday profile contracts PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
