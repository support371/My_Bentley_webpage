"""Regression checks: all Bentley user-management routes require administrator access.

This test inspects the route dependency graph without contacting external
accounts, modifying the database, or exercising production endpoints.
"""
from fastapi.routing import APIRoute
from app.api.routes.auth import router
from app.core.security import require_admin


def test_all_user_management_routes_require_admin():
    routes = [
        route for route in router.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/users")
    ]
    assert routes, "Expected user-management API routes"
    expected = {"GET", "POST", "PUT", "DELETE"}
    seen = set()
    for route in routes:
        seen.update(route.methods & expected)
        assert any(
            dependency.call is require_admin
            for dependency in route.dependant.dependencies
        ), f"Missing admin access requirement: {sorted(route.methods)} {route.path}"
    assert expected <= seen


def test_management_routes_are_not_public():
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api/users"):
            continue
        assert require_admin in {
            dependency.call for dependency in route.dependant.dependencies
        }
