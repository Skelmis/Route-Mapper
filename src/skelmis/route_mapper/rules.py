import dataclasses
from collections import defaultdict
from typing import Any

from skelmis.route_mapper import transform


@dataclasses.dataclass
class ImplicitRoutes:
    description: str = (
        "In C# if you define a public method on a controller it becomes "
        "an API route even without defining HTTP verbs or routes. All "
        "routes listed on this class are implicitly API routes which you can hit. "
        "Now depending on how the controller is defined, you may not actually be "
        "able to route to these in practice so make sure to try out each one. "
        "If there is a small number its likely exposed as a mistake and I "
        "would be calling it out in a report."
    )
    implicit_routes: list[transform.Route] = dataclasses.field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def get_implicit_routes(*api_classes: transform.APIClass) -> ImplicitRoutes:
    ir = ImplicitRoutes()
    for api_class in api_classes:
        for route in api_class.routes:
            if route.is_implicit_route:
                ir.implicit_routes.append(route)

    return ir

@dataclasses.dataclass
class AuthorisationPolicy:
    requires_authentication: bool
    applied_policies: list[str]
    routes: list[transform.Route]

@dataclasses.dataclass
class RoutesPerAuthorisationPolicy:
    description: str = (
        "This rule groups all routes together into groups based on "
        "the authorisation policies being applied to them. "
        "I quite like using this rule to find out what routes "
        "don't require authentication as well as what is admin "
        "gated and what isn't. If 'applied_policies' is empty "
        "then no authorisation checks are done and access is "
        "entirely based on the 'requires_authentication' field."
    )
    routes: list[AuthorisationPolicy]= dataclasses.field(default_factory=list)
    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

def get_routes_group_by_authz(*api_classes:transform.APIClass) -> RoutesPerAuthorisationPolicy:
    routes: dict[tuple[bool,frozenset[str]], list[transform.Route]] = defaultdict(list)
    for api_class in api_classes:
        for route in api_class.routes:
            if not route.requires_authentication:
                routes[(route.requires_authentication, frozenset())].append(route)
                continue

            policies = route.authorisation_policies
            policies.extend(route.inherited_authorisation_policies)
            policies = frozenset(sorted(policies, key=lambda p:len(p), reverse=True))
            routes[(route.requires_authentication, policies)].append(route)

    rp = RoutesPerAuthorisationPolicy()
    for k,v in routes.items():
        requires_authentication, policies = k
        rp.routes.append(AuthorisationPolicy(applied_policies=list(policies), routes=v,requires_authentication=requires_authentication))

    return rp