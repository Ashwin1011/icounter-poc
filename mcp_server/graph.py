from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from mcp_server.catalog import catalog
from mcp_server.errors import err
from mcp_server.settings import settings


NODE_LABELS = {
    "EMP": "Employee",
    "TEAM": "Team",
    "SVC": "Service",
    "PROD": "Product",
    "PROJ": "Project",
    "CUST": "Customer",
    "INC": "Incident",
    "TKT": "Ticket",
    "INFRA": "InfraComponent",
    "RB": "Runbook",
    "POL": "Policy",
}


def _label_for(entity_id: str) -> str:
    prefix = entity_id.split("-")[0]
    return NODE_LABELS.get(prefix, "Entity")


class GraphStore:
    def __init__(self) -> None:
        self._driver = None

    def connect(self) -> None:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def health(self) -> dict[str, Any]:
        try:
            self.connect()
            assert self._driver is not None
            self._driver.verify_connectivity()
            return {"ok": True, "service": "neo4j"}
        except Exception as exc:  # noqa: BLE001
            return err("database_unavailable", f"Neo4j is unavailable: {exc}", retryable=True)

    def _run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        self.connect()
        assert self._driver is not None
        with self._driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    def seed(self) -> dict[str, int]:
        catalog.reload()
        self.connect()
        assert self._driver is not None
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

            def upsert(entity_id: str, name: str, props: dict[str, Any] | None = None) -> None:
                label = _label_for(entity_id)
                payload = {"id": entity_id, "name": name}
                if props:
                    payload.update(props)
                session.run(
                    f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                    id=entity_id,
                    props=payload,
                )

            def rel(src: str, dest: str, typ: str) -> None:
                session.run(
                    f"""
                    MATCH (a {{id: $src}}), (b {{id: $dest}})
                    MERGE (a)-[r:{typ}]->(b)
                    """,
                    src=src,
                    dest=dest,
                )

            for emp in catalog.employees:
                upsert(emp["id"], emp["name"], {"title": emp["title"], "role": emp["role"]})
            for team in catalog.teams:
                upsert(team["id"], team["name"], {"oncall_rotation": team["oncall_rotation"]})
            for svc in catalog.services:
                upsert(svc["id"], svc["name"])
            for project in catalog.projects:
                upsert(project["id"], project["name"], {"status": project["status"]})
            for product in catalog.products:
                upsert(product["id"], product["name"])
            for customer in catalog.customers:
                upsert(customer["id"], customer["name"])
            for incident in catalog.incidents:
                upsert(
                    incident["id"],
                    incident["title"],
                    {"severity": incident["severity"], "date": incident["date"]},
                )
            for ticket in catalog.tickets:
                upsert(ticket["id"], ticket["title"], {"status": ticket["status"]})
            for infra in catalog.infrastructure:
                upsert(infra["id"], infra["name"], {"kind": infra["kind"], "status": infra["status"]})

            for emp in catalog.employees:
                rel(emp["id"], emp["team_id"], "MEMBER_OF")
            for team in catalog.teams:
                rel(team["manager_id"], team["id"], "MANAGES")
                for service_id in team["owns_services"]:
                    rel(team["id"], service_id, "OWNS")
                for project_id in team.get("owns_projects", []):
                    rel(team["id"], project_id, "OWNS")
            for svc in catalog.services:
                rel(svc["owner_team_id"], svc["id"], "OWNS")
                for dep in svc["depends_on"]:
                    rel(svc["id"], dep, "DEPENDS_ON")
                for product_id in svc["products"]:
                    rel(product_id, svc["id"], "USES")
            for project in catalog.projects:
                rel(project["technical_owner_id"], project["id"], "OWNS")
                rel(project["primary_team_id"], project["id"], "OWNS")
                for service_id in project["services"]:
                    rel(project["id"], service_id, "RELATES_TO")
                for dep in project["depends_on_projects"]:
                    rel(project["id"], dep, "DEPENDS_ON")
                for dep in project["depends_on_services"]:
                    rel(project["id"], dep, "DEPENDS_ON")
            for product in catalog.products:
                for service_id in product["services"]:
                    rel(product["id"], service_id, "USES")
                for customer_id in product["customers"]:
                    rel(customer_id, product["id"], "USES_PRODUCT")
            for customer in catalog.customers:
                for product_id in customer["products"]:
                    rel(customer["id"], product_id, "USES_PRODUCT")
                for service_id in customer["services"]:
                    rel(customer["id"], service_id, "USES")
                for incident_id in customer["incidents"]:
                    rel(incident_id, customer["id"], "AFFECTS")
            for incident in catalog.incidents:
                rel(incident["id"], incident["service_id"], "AFFECTS")
                rel(incident["owner_team_id"], incident["id"], "OWNS")
                if incident.get("commander_id"):
                    rel(incident["commander_id"], incident["id"], "COMMANDS")
                for customer_id in incident.get("customers", []):
                    rel(incident["id"], customer_id, "AFFECTS")
            for ticket in catalog.tickets:
                if ticket.get("service_id"):
                    rel(ticket["id"], ticket["service_id"], "TRACKS")
                if ticket.get("customer_id"):
                    rel(ticket["id"], ticket["customer_id"], "TRACKS")
                if ticket.get("related_incident_id"):
                    rel(ticket["id"], ticket["related_incident_id"], "RELATES_TO")
            for infra in catalog.infrastructure:
                for service_id in infra["service_ids"]:
                    rel(service_id, infra["id"], "DEPLOYED_ON")

        counts = self._run(
            """
            CALL {
              MATCH (n) RETURN count(n) AS nodes
            }
            CALL {
              MATCH ()-[r]->() RETURN count(r) AS rels
            }
            RETURN nodes, rels
            """
        )
        row = counts[0] if counts else {"nodes": 0, "rels": 0}
        return {"nodes": row["nodes"], "relationships": row["rels"]}

    def neighbors(self, entity_id: str, depth: int = 1) -> dict[str, Any]:
        resolved = catalog.resolve(entity_id) or entity_id
        depth = max(1, min(depth, 3))
        try:
            rows = self._run(
                f"""
                MATCH (n {{id: $id}})
                OPTIONAL MATCH (n)-[r*1..{depth}]-(m)
                WITH n, collect(DISTINCT {{
                  id: m.id,
                  name: coalesce(m.name, m.title),
                  labels: labels(m)
                }}) AS neighbors
                RETURN n.id AS id, coalesce(n.name, n.title) AS name, labels(n) AS labels, neighbors
                """,
                id=resolved,
            )
        except Neo4jError as exc:
            return err("database_unavailable", str(exc), retryable=True)
        if not rows:
            return err("not_found", f"Graph node '{resolved}' was not found.", id=resolved)
        payload = rows[0]
        payload["neighbors"] = [item for item in payload["neighbors"] if item.get("id")]
        return payload

    def shortest_path(self, source: str, target: str) -> dict[str, Any]:
        src = catalog.resolve(source) or source
        dst = catalog.resolve(target) or target
        try:
            rows = self._run(
                """
                MATCH (a {id: $src}), (b {id: $dst})
                MATCH p = shortestPath((a)-[*..6]-(b))
                RETURN [n IN nodes(p) | {id: n.id, name: coalesce(n.name, n.title), labels: labels(n)}] AS nodes,
                       [r IN relationships(p) | type(r)] AS relationships
                """,
                src=src,
                dst=dst,
            )
        except Neo4jError as exc:
            return err("database_unavailable", str(exc), retryable=True)
        if not rows:
            return err("not_found", f"No path found between '{src}' and '{dst}'.")
        return rows[0]

    def blast_radius(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        resolved = catalog.resolve(entity_id) or entity_id
        depth = max(1, min(depth, 4))
        try:
            rows = self._run(
                f"""
                MATCH (n {{id: $id}})
                OPTIONAL MATCH (n)-[:AFFECTS|DEPENDS_ON|USES|USES_PRODUCT|OWNS|RELATES_TO*1..{depth}]-(m)
                WITH n,
                     collect(DISTINCT m) AS reached
                RETURN n.id AS id,
                       coalesce(n.name, n.title) AS name,
                       [x IN reached WHERE x IS NOT NULL | {{
                         id: x.id,
                         name: coalesce(x.name, x.title),
                         labels: labels(x)
                       }}] AS impacted
                """,
                id=resolved,
            )
        except Neo4jError as exc:
            return err("database_unavailable", str(exc), retryable=True)
        if not rows:
            return err("not_found", f"Graph node '{resolved}' was not found.", id=resolved)
        return rows[0]

    def who_owns(self, entity_id: str) -> dict[str, Any]:
        resolved = catalog.resolve(entity_id) or entity_id
        try:
            rows = self._run(
                """
                MATCH (n {id: $id})
                OPTIONAL MATCH (owner)-[:OWNS]->(n)
                OPTIONAL MATCH (emp:Employee)-[:MEMBER_OF]->(owner)
                OPTIONAL MATCH (manager:Employee)-[:MANAGES]->(owner)
                RETURN n.id AS id,
                       coalesce(n.name, n.title) AS name,
                       collect(DISTINCT {id: owner.id, name: owner.name, labels: labels(owner)}) AS owners,
                       collect(DISTINCT {id: manager.id, name: manager.name, title: manager.title}) AS managers
                """,
                id=resolved,
            )
        except Neo4jError as exc:
            return err("database_unavailable", str(exc), retryable=True)
        if not rows:
            return err("not_found", f"Graph node '{resolved}' was not found.", id=resolved)
        payload = rows[0]
        payload["owners"] = [item for item in payload["owners"] if item.get("id")]
        payload["managers"] = [item for item in payload["managers"] if item.get("id")]
        return payload


graph = GraphStore()
