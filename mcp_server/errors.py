from typing import Any


def ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def err(code: str, message: str, *, retryable: bool = False, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error": message,
        "code": code,
        "retryable": retryable,
    }
    payload.update(extra)
    return payload


def not_found(entity: str, identifier: str) -> dict[str, Any]:
    return err("not_found", f"{entity} '{identifier}' was not found.", entity=entity, id=identifier)
