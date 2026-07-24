VERDICT_LABELS = {
    "must_read": "🔴 Must read",
    "worth_a_skim": "🟡 Worth a skim",
    "radar": "⚪ On your radar",
}


def format_authors(authors):
    text = ", ".join(authors[:3])
    if len(authors) > 3:
        text += ", et al."
    return text


def build_markdown(date_str, papers):
    lines = [f"# Daily Paper Digest — {date_str}", ""]
    if not papers:
        lines.append("*Nothing cleared the bar today — enjoy the free time.*")
        return "\n".join(lines)

    for i, p in enumerate(papers, start=1):
        verdict = VERDICT_LABELS.get(p["verdict"], p["verdict"])
        tags = " ".join(f"`{t}`" for t in p["topics"])
        lines.append(f"## {i}. {p['title']}")
        lines.append(
            f"{verdict} · **worth {p['worth_score']}/10** · "
            f"*{format_authors(p['authors'])}* — [{p['id']}]({p['url']})"
        )
        if tags:
            lines.append(tags)
        lines.append("")
        lines.append(p["tldr"])
        lines.append("")
        lines.append(f"**Why it matters:** {p['why_it_matters']}")
        lines.append("")
    return "\n".join(lines)
