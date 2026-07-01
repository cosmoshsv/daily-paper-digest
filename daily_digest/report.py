def build_markdown(date_str, papers):
    lines = [f"# Daily Paper Digest — {date_str}", ""]
    for i, p in enumerate(papers, start=1):
        authors = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors += ", et al."
        lines.append(f"## {i}. {p['title']}")
        lines.append(f"*{authors}* — [{p['id']}]({p['url']})")
        lines.append("")
        lines.append(p["summary_short"])
        lines.append("")
        lines.append(f"**Why it matters:** {p['why_it_matters']}")
        lines.append("")
    return "\n".join(lines)
