from __future__ import annotations

from typing import Any

DEMO_USERS: dict[str, dict[str, Any]] = {
    "sameer.kulkarni": {
        "user_id": "sameer.kulkarni",
        "name": "Sameer Kulkarni",
        "role": "Technical Lead, SRE",
        "team": "TEAM-SRE",
        "seed_memories": [
            {"key": "role", "value": "SRE technical lead and frequent incident commander", "source": "profile"},
            {"key": "focus", "value": "reliability, blast radius, and runbooks", "source": "profile"},
        ],
    },
    "mei.wong": {
        "user_id": "mei.wong",
        "name": "Mei Wong",
        "role": "Technical Lead, Customer Experience",
        "team": "TEAM-CX",
        "seed_memories": [
            {"key": "role", "value": "CX technical lead and Project Apollo owner", "source": "profile"},
            {"key": "focus", "value": "notifications, customer impact, Project Apollo", "source": "profile"},
        ],
    },
    "rohan.iyer": {
        "user_id": "rohan.iyer",
        "name": "Rohan Iyer",
        "role": "Manager, Customer Experience",
        "team": "TEAM-CX",
        "seed_memories": [
            {"key": "role", "value": "CX manager and Apollo executive sponsor", "source": "profile"},
            {"key": "focus", "value": "project status, ownership, and customer-facing risk", "source": "profile"},
        ],
    },
}


def get_user(user_id: str) -> dict[str, Any] | None:
    return DEMO_USERS.get(user_id)


def require_user(user_id: str) -> dict[str, Any]:
    user = get_user(user_id)
    if not user:
        raise KeyError(user_id)
    return user
