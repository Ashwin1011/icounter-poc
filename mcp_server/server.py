from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server.catalog import catalog
from mcp_server.errors import err, not_found, ok
from mcp_server.graph import graph
from mcp_server.rag import rag
from mcp_server.settings import settings

mcp = FastMCP(
    "nexora-mcp",
    instructions="Enterprise tools for Nexora projects, teams, services, incidents, tickets, customers, infrastructure, documentation, and the relationship graph.",
)


def _fail_if_requested() -> dict[str, Any] | None:
    mode = os.environ.get("NEXORA_FAIL", settings.fail_mode)
    if mode == "tools":
        return err("tool_failure", "Simulated tool failure.", retryable=True)
    if mode == "db":
        return err("database_unavailable", "Simulated database failure.", retryable=True)
    return None


def _guard() -> dict[str, Any] | None:
    return _fail_if_requested()


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    neo = graph.health()
    qdr = rag.health()
    status = "ok" if neo.get("ok") and qdr.get("ok") else "degraded"
    return JSONResponse(
        {
            "status": status,
            "service": "nexora-mcp",
            "neo4j": neo,
            "qdrant": qdr,
            "tools": 38,
        }
    )


# --- Projects ---


@mcp.tool
def get_project(project_id: str) -> dict[str, Any]:
    """Get a Nexora project by id or name (for example PROJ-APOLLO or Apollo)."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.project_by_id, project_id)
    return ok(row) if row else not_found("project", project_id)


@mcp.tool
def list_projects() -> dict[str, Any]:
    """List all Nexora projects and their owners, teams, and services."""
    if guarded := _guard():
        return guarded
    return ok(catalog.projects)


@mcp.tool
def get_project_dependencies(project_id: str) -> dict[str, Any]:
    """List project and service dependencies for a project."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.project_by_id, project_id)
    if not row:
        return not_found("project", project_id)
    return ok(
        {
            "project_id": row["id"],
            "depends_on_projects": row.get("depends_on_projects", []),
            "depends_on_services": row.get("depends_on_services", []),
            "services": row.get("services", []),
        }
    )


@mcp.tool
def get_projects_for_team(team_id: str) -> dict[str, Any]:
    """List projects owned by a team."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(team_id) or team_id
    rows = [row for row in catalog.projects if row["primary_team_id"] == resolved]
    return ok(rows)


@mcp.tool
def get_projects_for_service(service_id: str) -> dict[str, Any]:
    """List projects that involve a service."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(service_id) or service_id
    rows = [row for row in catalog.projects if resolved in row.get("services", [])]
    return ok(rows)


# --- Teams / employees ---


@mcp.tool
def get_team(team_id: str) -> dict[str, Any]:
    """Get a team by id or name."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.team_by_id, team_id)
    return ok(row) if row else not_found("team", team_id)


@mcp.tool
def list_teams() -> dict[str, Any]:
    """List all Nexora teams."""
    if guarded := _guard():
        return guarded
    return ok(catalog.teams)


@mcp.tool
def get_team_members(team_id: str) -> dict[str, Any]:
    """List employees on a team."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(team_id) or team_id
    if resolved not in catalog.team_by_id:
        return not_found("team", team_id)
    rows = [row for row in catalog.employees if row["team_id"] == resolved]
    return ok(rows)


@mcp.tool
def get_employee(employee_id: str) -> dict[str, Any]:
    """Get an employee by id or name."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.employee_by_id, employee_id)
    return ok(row) if row else not_found("employee", employee_id)


@mcp.tool
def list_employees() -> dict[str, Any]:
    """List all employees in the Nexora catalog."""
    if guarded := _guard():
        return guarded
    return ok(catalog.employees)


@mcp.tool
def get_oncall_for_team(team_id: str) -> dict[str, Any]:
    """Get the primary on-call rotation and current technical lead for a team."""
    if guarded := _guard():
        return guarded
    team = catalog.get(catalog.team_by_id, team_id)
    if not team:
        return not_found("team", team_id)
    lead = catalog.employee_by_id.get(team["tech_lead_id"])
    return ok(
        {
            "team_id": team["id"],
            "rotation": team["oncall_rotation"],
            "primary_oncall": lead,
        }
    )


# --- Services ---


@mcp.tool
def get_service(service_id: str) -> dict[str, Any]:
    """Get a service by id or name (for example SVC-PAY or Payment Service)."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.service_by_id, service_id)
    return ok(row) if row else not_found("service", service_id)


@mcp.tool
def list_services() -> dict[str, Any]:
    """List all platform services."""
    if guarded := _guard():
        return guarded
    return ok(catalog.services)


@mcp.tool
def get_service_owner(service_id: str) -> dict[str, Any]:
    """Get the owning team and leads for a service."""
    if guarded := _guard():
        return guarded
    service = catalog.get(catalog.service_by_id, service_id)
    if not service:
        return not_found("service", service_id)
    team = catalog.team_by_id.get(service["owner_team_id"])
    return ok(
        {
            "service": service,
            "team": team,
            "manager": catalog.employee_by_id.get((team or {}).get("manager_id", "")),
            "tech_lead": catalog.employee_by_id.get((team or {}).get("tech_lead_id", "")),
        }
    )


@mcp.tool
def get_service_dependencies(service_id: str) -> dict[str, Any]:
    """List services this service depends on."""
    if guarded := _guard():
        return guarded
    service = catalog.get(catalog.service_by_id, service_id)
    if not service:
        return not_found("service", service_id)
    deps = [catalog.service_by_id.get(item, {"id": item}) for item in service.get("depends_on", [])]
    return ok({"service_id": service["id"], "depends_on": deps})


@mcp.tool
def get_service_dependents(service_id: str) -> dict[str, Any]:
    """List services that depend on this service."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(service_id) or service_id
    if resolved not in catalog.service_by_id:
        return not_found("service", service_id)
    rows = [row for row in catalog.services if resolved in row.get("depends_on", [])]
    return ok(rows)


# --- Incidents ---


@mcp.tool
def get_incident(incident_id: str) -> dict[str, Any]:
    """Get an incident by id (for example INC-1001)."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.incident_by_id, incident_id)
    return ok(row) if row else not_found("incident", incident_id)


@mcp.tool
def list_incidents(severity: str | None = None) -> dict[str, Any]:
    """List incidents, optionally filtered by severity such as Sev-1."""
    if guarded := _guard():
        return guarded
    rows = catalog.incidents
    if severity:
        rows = [row for row in rows if row["severity"].lower() == severity.lower()]
    rows = sorted(rows, key=lambda row: row["date"], reverse=True)
    return ok(rows)


@mcp.tool
def get_incidents_for_service(service_id: str) -> dict[str, Any]:
    """List incidents that primarily affected a service, newest first."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(service_id) or service_id
    if resolved not in catalog.service_by_id:
        return not_found("service", service_id)
    rows = [row for row in catalog.incidents if row["service_id"] == resolved]
    rows = sorted(rows, key=lambda row: row["date"], reverse=True)
    return ok(rows)


@mcp.tool
def get_incidents_for_customer(customer_id: str) -> dict[str, Any]:
    """List incidents that impacted a customer."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(customer_id) or customer_id
    if resolved not in catalog.customer_by_id:
        return not_found("customer", customer_id)
    rows = [row for row in catalog.incidents if resolved in row.get("customers", [])]
    return ok(rows)


# --- Tickets ---


@mcp.tool
def get_ticket(ticket_id: str) -> dict[str, Any]:
    """Get a ticket by id (for example TKT-2401)."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.ticket_by_id, ticket_id)
    return ok(row) if row else not_found("ticket", ticket_id)


@mcp.tool
def list_tickets(status: str | None = None) -> dict[str, Any]:
    """List tickets, optionally filtered by status."""
    if guarded := _guard():
        return guarded
    rows = catalog.tickets
    if status:
        rows = [row for row in rows if row["status"].lower() == status.lower()]
    return ok(rows)


@mcp.tool
def get_tickets_for_service(service_id: str) -> dict[str, Any]:
    """List tickets associated with a service."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(service_id) or service_id
    rows = [row for row in catalog.tickets if row.get("service_id") == resolved]
    return ok(rows)


@mcp.tool
def create_ticket(
    title: str,
    service_id: str,
    summary: str,
    priority: str = "P3",
    customer_id: str | None = None,
) -> dict[str, Any]:
    """Create a follow-up ticket for a service. This is the only write tool."""
    if guarded := _guard():
        return guarded
    service = catalog.get(catalog.service_by_id, service_id)
    if not service:
        return not_found("service", service_id)
    existing_ids = [row["id"] for row in catalog.tickets]
    next_num = 2400 + len(existing_ids) + 1
    ticket = {
        "id": f"TKT-{next_num}",
        "title": title,
        "status": "open",
        "priority": priority,
        "service_id": service["id"],
        "customer_id": catalog.resolve(customer_id) if customer_id else None,
        "project_id": None,
        "assignee_id": None,
        "related_incident_id": None,
        "summary": summary,
    }
    catalog.persist_ticket(ticket)
    return ok(ticket)


# --- Customers / products ---


@mcp.tool
def get_customer(customer_id: str) -> dict[str, Any]:
    """Get a customer by id or name."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.customer_by_id, customer_id)
    return ok(row) if row else not_found("customer", customer_id)


@mcp.tool
def list_customers() -> dict[str, Any]:
    """List all customers."""
    if guarded := _guard():
        return guarded
    return ok(catalog.customers)


@mcp.tool
def get_customer_products(customer_id: str) -> dict[str, Any]:
    """List products used by a customer."""
    if guarded := _guard():
        return guarded
    customer = catalog.get(catalog.customer_by_id, customer_id)
    if not customer:
        return not_found("customer", customer_id)
    products = [catalog.product_by_id.get(item, {"id": item}) for item in customer.get("products", [])]
    return ok(products)


@mcp.tool
def get_product(product_id: str) -> dict[str, Any]:
    """Get a product by id or name (CommerceCloud, BillingPro, SupportHub)."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.product_by_id, product_id)
    return ok(row) if row else not_found("product", product_id)


@mcp.tool
def list_products() -> dict[str, Any]:
    """List all products."""
    if guarded := _guard():
        return guarded
    return ok(catalog.products)


@mcp.tool
def get_product_services(product_id: str) -> dict[str, Any]:
    """List services that support a product."""
    if guarded := _guard():
        return guarded
    product = catalog.get(catalog.product_by_id, product_id)
    if not product:
        return not_found("product", product_id)
    services = [catalog.service_by_id.get(item, {"id": item}) for item in product.get("services", [])]
    return ok(services)


# --- Infrastructure ---


@mcp.tool
def get_infra_component(component_id: str) -> dict[str, Any]:
    """Get an infrastructure component by id or name."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.infra_by_id, component_id)
    return ok(row) if row else not_found("infra", component_id)


@mcp.tool
def list_infra_components() -> dict[str, Any]:
    """List infrastructure components."""
    if guarded := _guard():
        return guarded
    return ok(catalog.infrastructure)


@mcp.tool
def get_infra_for_service(service_id: str) -> dict[str, Any]:
    """List infrastructure that a service is deployed on."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(service_id) or service_id
    if resolved not in catalog.service_by_id:
        return not_found("service", service_id)
    rows = [row for row in catalog.infrastructure if resolved in row.get("service_ids", [])]
    return ok(rows)


@mcp.tool
def get_slo_for_service(service_id: str) -> dict[str, Any]:
    """Get SLO targets for a service."""
    if guarded := _guard():
        return guarded
    resolved = catalog.resolve(service_id) or service_id
    row = catalog.slo_by_service.get(resolved)
    return ok(row) if row else not_found("slo", service_id)


# --- Documentation ---


@mcp.tool
def search_documentation(query: str, limit: int = 5, category: str | None = None) -> dict[str, Any]:
    """Semantic search over Nexora documents. Returns snippets and citations."""
    if guarded := _guard():
        return guarded
    result = rag.search(query, limit=limit, category=category)
    if result.get("ok") is False:
        return result
    return ok(result)


@mcp.tool
def get_document(path: str) -> dict[str, Any]:
    """Read a knowledge-base document by relative path, such as runbooks/payment-database-failure.md."""
    if guarded := _guard():
        return guarded
    if ".." in path or path.startswith("/"):
        return err("invalid_request", "Document path must be a relative knowledge-base path.")
    text = catalog.read_document(path)
    if text is None:
        return not_found("document", path)
    return ok({"path": path, "text": text})


@mcp.tool
def get_runbook_for_service(service_id: str) -> dict[str, Any]:
    """Get the operational runbook for a service, including document text."""
    if guarded := _guard():
        return guarded
    service = catalog.get(catalog.service_by_id, service_id)
    if not service:
        return not_found("service", service_id)
    matches = [row for row in catalog.runbooks if service["id"] in row.get("service_ids", [])]
    documents = []
    for row in matches:
        text = catalog.read_document(row["path"])
        documents.append({**row, "text": text})
    if not documents:
        return err("not_found", f"No runbook is registered for {service['id']}.")
    return ok(documents)


@mcp.tool
def get_policy(policy_id: str) -> dict[str, Any]:
    """Get a policy by id or title, including document text."""
    if guarded := _guard():
        return guarded
    row = catalog.get(catalog.policy_by_id, policy_id)
    if not row:
        lowered = policy_id.lower()
        row = next((item for item in catalog.policies if lowered in item["title"].lower()), None)
    if not row:
        return not_found("policy", policy_id)
    text = catalog.read_document(row["path"])
    return ok({**row, "text": text})


# --- Graph ---


@mcp.tool
def graph_neighbors(entity_id: str, depth: int = 1) -> dict[str, Any]:
    """Return nearby graph nodes for an entity."""
    if guarded := _guard():
        return guarded
    result = graph.neighbors(entity_id, depth=depth)
    return result if result.get("ok") is False else ok(result)


@mcp.tool
def graph_shortest_path(source_id: str, target_id: str) -> dict[str, Any]:
    """Return the shortest relationship path between two entities."""
    if guarded := _guard():
        return guarded
    result = graph.shortest_path(source_id, target_id)
    return result if result.get("ok") is False else ok(result)


@mcp.tool
def graph_blast_radius(entity_id: str, depth: int = 2) -> dict[str, Any]:
    """Return entities impacted by or related to an incident, service, or other node."""
    if guarded := _guard():
        return guarded
    result = graph.blast_radius(entity_id, depth=depth)
    return result if result.get("ok") is False else ok(result)


@mcp.tool
def graph_who_owns(entity_id: str) -> dict[str, Any]:
    """Return owning teams, managers, and related owners for an entity."""
    if guarded := _guard():
        return guarded
    result = graph.who_owns(entity_id)
    return result if result.get("ok") is False else ok(result)


def main() -> None:
    from scripts.bootstrap import main as bootstrap

    print("Bootstrapping Neo4j and Qdrant...")
    bootstrap()
    print("Starting MCP HTTP server...")
    mcp.run(transport="http", host="0.0.0.0", port=settings.mcp_port)


if __name__ == "__main__":
    main()
