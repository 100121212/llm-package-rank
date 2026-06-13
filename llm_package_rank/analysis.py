from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Iterable


MENTION_RE = re.compile(r"(?<![\w.-])([A-Za-z][A-Za-z0-9_.-]{1,60})(?![\w.-])")

STOP_WORDS = {
    "API",
    "CLI",
    "CSS",
    "CSV",
    "HTML",
    "HTTP",
    "JSON",
    "LLM",
    "MVP",
    "Python",
    "README",
    "SQL",
    "TypeScript",
    "UI",
    "URL",
}


@dataclass(frozen=True)
class Package:
    name: str
    ecosystem: str
    stars: int
    last_release: str
    open_issues: int
    funding: bool
    aliases: tuple[str, ...]

    def days_since_release(self, as_of_date: date) -> int:
        released = datetime.fromisoformat(self.last_release).date()
        return (as_of_date - released).days

    def maintenance_score(self, as_of_date: date) -> float:
        release_score = max(0.0, 1.0 - (self.days_since_release(as_of_date) / 730.0))
        issue_penalty = min(0.35, self.open_issues / 1000.0)
        funding_bonus = 0.1 if self.funding else 0.0
        return round(max(0.0, min(1.0, release_score - issue_penalty + funding_bonus)), 3)


@dataclass(frozen=True)
class Recommendation:
    task_id: str
    model: str
    package: str
    raw_name: str


def load_packages(raw_packages: Iterable[dict]) -> dict[str, Package]:
    packages: dict[str, Package] = {}
    for item in raw_packages:
        package = Package(
            name=item["name"],
            ecosystem=item.get("ecosystem", "unknown"),
            stars=int(item.get("stars", 0)),
            last_release=item["last_release"],
            open_issues=int(item.get("open_issues", 0)),
            funding=bool(item.get("funding", False)),
            aliases=tuple(item.get("aliases", [])),
        )
        packages[package.name.lower()] = package
        for alias in package.aliases:
            packages[alias.lower()] = package
    return packages


def extract_recommendations(responses: Iterable[dict], packages: dict[str, Package]) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    for response in responses:
        text = response.get("answer", "")
        seen_in_answer: set[str] = set()
        for match in MENTION_RE.finditer(text):
            raw = match.group(1).strip("`.,:;()[]{}")
            if raw in STOP_WORDS:
                continue
            package = packages.get(raw.lower())
            if not package or package.name in seen_in_answer:
                continue
            seen_in_answer.add(package.name)
            recommendations.append(
                Recommendation(
                    task_id=response["task_id"],
                    model=response["model"],
                    package=package.name,
                    raw_name=raw,
                )
            )
    return recommendations


def analyze(tasks: list[dict], raw_packages: list[dict], responses: list[dict], as_of_date: date | None = None) -> dict:
    as_of_date = as_of_date or date.today()
    package_index = load_packages(raw_packages)
    canonical_packages = {package.name: package for package in package_index.values()}
    recommendations = extract_recommendations(responses, package_index)
    total_answers = max(1, len(responses))

    counts: dict[str, int] = {}
    by_task: dict[str, dict[str, int]] = {task["id"]: {} for task in tasks}
    by_model: dict[str, dict[str, int]] = {}
    for rec in recommendations:
        counts[rec.package] = counts.get(rec.package, 0) + 1
        by_task.setdefault(rec.task_id, {})[rec.package] = by_task.setdefault(rec.task_id, {}).get(rec.package, 0) + 1
        by_model.setdefault(rec.model, {})[rec.package] = by_model.setdefault(rec.model, {}).get(rec.package, 0) + 1

    rows = []
    for name, package in sorted(canonical_packages.items()):
        mentions = counts.get(name, 0)
        recommendation_share = round(mentions / total_answers, 3)
        maintenance_score = package.maintenance_score(as_of_date)
        visibility_gap = round(maintenance_score - recommendation_share, 3)
        stale_attention = recommendation_share > 0 and maintenance_score < 0.35
        overlooked = mentions == 0 and maintenance_score >= 0.65
        rows.append(
            {
                "package": name,
                "ecosystem": package.ecosystem,
                "mentions": mentions,
                "recommendation_share": recommendation_share,
                "maintenance_score": maintenance_score,
                "visibility_gap": visibility_gap,
                "stale_attention": stale_attention,
                "overlooked": overlooked,
                "stars": package.stars,
                "last_release": package.last_release,
                "funding": package.funding,
            }
        )

    rows.sort(key=lambda row: (-row["mentions"], -row["maintenance_score"], row["package"].lower()))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of_date": as_of_date.isoformat(),
        "task_count": len(tasks),
        "response_count": len(responses),
        "recommendation_count": len(recommendations),
        "packages": rows,
        "by_task": by_task,
        "by_model": by_model,
    }
