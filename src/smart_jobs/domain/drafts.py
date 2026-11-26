import hashlib
import json


def draft_content_hash(content: str, claims: list[tuple[str, list[str]]]) -> str:
    canonical = json.dumps(
        {
            "content": content,
            "claims": [
                {
                    "statement": statement,
                    "fact_ids": sorted(fact_ids),
                }
                for statement, fact_ids in claims
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
