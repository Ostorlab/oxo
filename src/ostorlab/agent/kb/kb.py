"""KB provides automatic mapping from the KB entry folder name to the meta content."""
import dataclasses
import json
import pathlib

from typing import Dict

KB_FOLDER = 'KB'
META_JSON = 'meta.json'
DESCRIPTION = 'description.md'
RECOMMENDATION = 'recommendation.md'


@dataclasses.dataclass
class Entry:
    """KB entry with information like title, risk rating and description."""
    title: str
    risk_rating: str
    references: Dict[str, str]
    short_description: str = ''
    description: str = ''
    recommendation: str = ''
    security_issue: bool = False
    privacy_issue: bool = False
    has_public_exploit: bool = False
    targeted_by_malware: bool = False
    targeted_by_ransomware: bool = False
    targeted_by_nation_state: bool = False
    cvss_v3_vector: str = ''


class MetaKB(type):
    """Handles KB mapping to appropriate folder."""

    def __getattr__(cls, item):
        kb_path = pathlib.Path(__file__).parent / KB_FOLDER / item

        if not (kb_path / META_JSON).exists():
            raise ValueError(f'{kb_path} does not have a mapping.')
        with (kb_path / META_JSON).open(encoding='utf-8') as f, (kb_path / DESCRIPTION).open(encoding='utf-8') as d, (
                kb_path / RECOMMENDATION).open(encoding='utf-8') as r:
            meta = json.loads(f.read())
            return Entry(
                title=meta.get('title'),
                risk_rating=meta.get('risk_rating'),
                short_description=meta.get('short_description'),
                description=d.read(),
                recommendation=r.read(),
                references=meta.get('references'),
                security_issue=meta.get('security_issue', False),
                privacy_issue=meta.get('privacy_issue', False),
                has_public_exploit=meta.get('has_public_exploit', False),
                targeted_by_malware=meta.get('targeted_by_malware', False),
                targeted_by_ransomware=meta.get('targeted_by_ransomware', False),
                targeted_by_nation_state=meta.get('targeted_by_nation_state', False),
                cvss_v3_vector=meta.get('cvss_v3_vector', ''),
            )


class KB(object, metaclass=MetaKB):
    """Vulnerability knowledge base dispatcher."""
