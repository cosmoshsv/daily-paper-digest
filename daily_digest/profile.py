import os

import yaml

PROFILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profile.yaml"
)


def load_profile(path=None):
    """Load the user's interest profile from profile.yaml.

    Returns {"topics": [{"name", "note"?}], "always_show": [...],
    "not_interested": [...]} with missing sections defaulted to empty.
    """
    path = path or PROFILE_PATH
    if not os.path.exists(path):
        raise SystemExit(
            f"Profile not found at {path}. Create a profile.yaml listing your "
            "topics of interest (see README)."
        )
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    topics = []
    for entry in data.get("topics") or []:
        if isinstance(entry, str):
            topics.append({"name": entry})
        elif isinstance(entry, dict) and entry.get("name"):
            topics.append({"name": entry["name"], **({"note": entry["note"]} if entry.get("note") else {})})

    if not topics:
        raise SystemExit(
            f"Profile at {path} has no topics. Add at least one under 'topics:'."
        )

    return {
        "topics": topics,
        "always_show": data.get("always_show") or [],
        "not_interested": data.get("not_interested") or [],
    }


def render_profile(profile):
    """Render the profile as text for inclusion in a ranking prompt."""
    lines = ["Topics I'm actively learning right now:"]
    for t in profile["topics"]:
        note = f" ({t['note']})" if t.get("note") else ""
        lines.append(f"- {t['name']}{note}")
    if profile["always_show"]:
        lines.append("\nAlways worth surfacing regardless of topic:")
        lines.extend(f"- {item}" for item in profile["always_show"])
    if profile["not_interested"]:
        lines.append("\nNot interested in:")
        lines.extend(f"- {item}" for item in profile["not_interested"])
    return "\n".join(lines)
