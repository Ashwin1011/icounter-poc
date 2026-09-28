from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_server.settings import settings


def _load(name: str) -> list[dict[str, Any]]:
    path = settings.structured_dir / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in rows if "id" in row}


class Catalog:
    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.employees = _load("employees.json")
        self.teams = _load("teams.json")
        self.services = _load("services.json")
        self.projects = _load("projects.json")
        self.products = _load("products.json")
        self.customers = _load("customers.json")
        self.incidents = _load("incidents.json")
        self.tickets = _load("tickets.json") + self._runtime_tickets()
        self.infrastructure = _load("infrastructure.json")
        self.slos = _load("slos.json")
        self.runbooks = _load("runbooks.json")
        self.policies = _load("policies.json")

        self.employee_by_id = _index(self.employees)
        self.team_by_id = _index(self.teams)
        self.service_by_id = _index(self.services)
        self.project_by_id = _index(self.projects)
        self.product_by_id = _index(self.products)
        self.customer_by_id = _index(self.customers)
        self.incident_by_id = _index(self.incidents)
        self.ticket_by_id = _index(self.tickets)
        self.infra_by_id = _index(self.infrastructure)
        self.slo_by_service = {row["service_id"]: row for row in self.slos}
        self.runbook_by_id = _index(self.runbooks)
        self.policy_by_id = _index(self.policies)

        self._alias = self._build_aliases()

    def _runtime_tickets(self) -> list[dict[str, Any]]:
        path = settings.runtime_dir / "tickets_created.json"
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def persist_ticket(self, ticket: dict[str, Any]) -> None:
        settings.runtime_dir.mkdir(parents=True, exist_ok=True)
        path = settings.runtime_dir / "tickets_created.json"
        existing = self._runtime_tickets()
        existing = [row for row in existing if row.get("id") != ticket["id"]]
        existing.append(ticket)
        path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        self.reload()

    def _build_aliases(self) -> dict[str, str]:
        aliases: dict[str, str] = {}
        collections = [
            self.employees,
            self.teams,
            self.services,
            self.projects,
            self.products,
            self.customers,
            self.incidents,
            self.tickets,
            self.infrastructure,
            self.runbooks,
            self.policies,
        ]
        for rows in collections:
            for row in rows:
                entity_id = str(row.get("id", "")).strip()
                name = str(row.get("name") or row.get("title") or "").strip()
                if entity_id:
                    aliases[entity_id.lower()] = entity_id
                    aliases[entity_id.split("-")[-1].lower()] = entity_id
                if name:
                    aliases[name.lower()] = entity_id
                    aliases[name.lower().replace("project ", "")] = entity_id
                    aliases[name.lower().replace(" service", "")] = entity_id
        extra = {
            "apollo": "PROJ-APOLLO",
            "orion": "PROJ-ORION",
            "atlas": "PROJ-ATLAS",
            "mercury": "PROJ-MERCURY",
            "payment": "SVC-PAY",
            "payments": "SVC-PAY",
            "payment service": "SVC-PAY",
            "identity": "SVC-ID",
            "identity service": "SVC-ID",
            "gateway": "SVC-GW",
            "api gateway": "SVC-GW",
            "orders": "SVC-ORD",
            "order service": "SVC-ORD",
            "notification": "SVC-NOTIFY",
            "notifications": "SVC-NOTIFY",
            "search": "SVC-SEARCH",
            "profile": "SVC-CUST",
            "customer profile": "SVC-CUST",
            "data platform": "SVC-DATA",
            "commercecloud": "PROD-COM",
            "billingpro": "PROD-BILL",
            "supporthub": "PROD-SUP",
            "northstar": "CUST-NORTHSTAR",
            "bluepeak": "CUST-BLUEPEAK",
            "greenleaf": "CUST-GREENLEAF",
            "redwood": "CUST-REDWOOD",
        }
        aliases.update(extra)
        return aliases

    def resolve(self, value: str | None) -> str | None:
        if not value:
            return None
        raw = value.strip()
        if not raw:
            return None
        return self._alias.get(raw.lower(), raw)

    def get(self, mapping: dict[str, dict[str, Any]], identifier: str) -> dict[str, Any] | None:
        resolved = self.resolve(identifier) or identifier
        return mapping.get(resolved)

    def knowledge_path(self, relative: str) -> Path:
        return settings.knowledge_dir / relative

    def read_document(self, relative: str) -> str | None:
        path = self.knowledge_path(relative)
        if not path.exists() or not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def list_documents(self) -> list[dict[str, str]]:
        root = settings.knowledge_dir
        if not root.exists():
            return []
        docs = []
        for path in sorted(root.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            docs.append({"path": rel, "category": rel.split("/")[0], "title": path.stem})
        return docs


catalog = Catalog()
