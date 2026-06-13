from __future__ import annotations


def render_markdown(result: dict) -> str:
    packages = result["packages"]
    overlooked = [row for row in packages if row["overlooked"]]
    stale = [row for row in packages if row["stale_attention"]]

    lines = [
        "# LLM Package Rank Report",
        "",
        f"- Generated: `{result['generated_at']}`",
        f"- Scored as of: `{result['as_of_date']}`",
        f"- Tasks: `{result['task_count']}`",
        f"- Model answers: `{result['response_count']}`",
        f"- Extracted recommendations: `{result['recommendation_count']}`",
        "",
        "## Package Visibility",
        "",
        "| Package | Mentions | Share | Maintenance | Gap | Flags |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]

    for row in packages:
        flags = []
        if row["overlooked"]:
            flags.append("overlooked")
        if row["stale_attention"]:
            flags.append("stale attention")
        if row["funding"]:
            flags.append("funding")
        lines.append(
            "| {package} | {mentions} | {share:.3f} | {maintenance:.3f} | {gap:.3f} | {flags} |".format(
                package=row["package"],
                mentions=row["mentions"],
                share=row["recommendation_share"],
                maintenance=row["maintenance_score"],
                gap=row["visibility_gap"],
                flags=", ".join(flags) or "-",
            )
        )

    lines.extend(["", "## Findings", ""])
    if overlooked:
        names = ", ".join(row["package"] for row in overlooked)
        lines.append(f"- High-maintenance packages with no recommendations: {names}.")
    else:
        lines.append("- No high-maintenance packages were fully invisible in this run.")

    if stale:
        names = ", ".join(row["package"] for row in stale)
        lines.append(f"- Stale packages still receiving model attention: {names}.")
    else:
        lines.append("- No low-maintenance packages received stale attention in this run.")

    lines.extend(
        [
            "",
            "## Task Breakdown",
            "",
        ]
    )
    for task_id, counts in sorted(result["by_task"].items()):
        visible = ", ".join(f"{name} ({count})" for name, count in sorted(counts.items())) or "none"
        lines.append(f"- `{task_id}`: {visible}")

    return "\n".join(lines) + "\n"
