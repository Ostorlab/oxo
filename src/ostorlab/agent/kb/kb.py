"""KB provides automatic mapping from the KB entry folder name to the meta content."""

import dataclasses
import json
import pathlib

from typing import Dict, Optional, Union

KB_FOLDER = "KB"
META_JSON = "meta.json"
DESCRIPTION = "description.md"
RECOMMENDATION = "recommendation.md"


@dataclasses.dataclass
class Entry:
    """KB entry with information like title, risk rating and description."""

    title: str
    risk_rating: str
    references: Dict[str, str]
    short_description: str = ""
    description: str = ""
    recommendation: str = ""
    security_issue: bool = False
    privacy_issue: bool = False
    has_public_exploit: bool = False
    targeted_by_malware: bool = False
    targeted_by_ransomware: bool = False
    targeted_by_nation_state: bool = False
    cvss_v3_vector: str = ""
    cvss_v4_vector: str = ""
    category_groups: Optional[list[dict[str, Union[str, list[str]]]]] = None


class MetaKB(type):
    """Handles KB mapping to appropriate folder."""

    def __getattr__(cls, item: str) -> Entry:
        kb_path = pathlib.Path(__file__).parent / KB_FOLDER
        paths = [f for f in kb_path.glob(f"**/{item}") if f.is_dir()]
        if not paths:
            raise ValueError(f"{item} does not exists.")
        entry_path = paths[0]
        if not (entry_path / META_JSON).exists():
            raise ValueError(f"{entry_path} does not have a mapping.")
        with (entry_path / META_JSON).open(encoding="utf-8") as f, (
            entry_path / DESCRIPTION
        ).open(encoding="utf-8") as d, (entry_path / RECOMMENDATION).open(
            encoding="utf-8"
        ) as r:
            meta = json.loads(f.read())
            categories = meta.get("categories", {})
            category_groups = [
                {"key": k, "categories": v} for k, v in categories.items()
            ]

            return Entry(
                title=meta.get("title"),
                risk_rating=meta.get("risk_rating"),
                short_description=meta.get("short_description"),
                description=d.read(),
                recommendation=r.read(),
                references=meta.get("references"),
                security_issue=meta.get("security_issue", False),
                privacy_issue=meta.get("privacy_issue", False),
                has_public_exploit=meta.get("has_public_exploit", False),
                targeted_by_malware=meta.get("targeted_by_malware", False),
                targeted_by_ransomware=meta.get("targeted_by_ransomware", False),
                targeted_by_nation_state=meta.get("targeted_by_nation_state", False),
                cvss_v3_vector=meta.get("cvss_v3_vector", ""),
                cvss_v4_vector=meta.get("cvss_v4_vector", ""),
                category_groups=category_groups,
            )


class KB(object, metaclass=MetaKB):
    """Vulnerability knowledge base dispatcher."""
