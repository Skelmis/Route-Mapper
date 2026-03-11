import dataclasses
from typing import Any

from skelmis.route_mapper import ast


@dataclasses.dataclass
class Attribute:
    # [ApiController]
    # [Route("/api/[controller]")]
    # etc`s
    name: str
    arguments: list[str]


@dataclasses.dataclass
class Argument:
    argument_type: str
    argument_name: str
    is_nullable: bool
    has_default_argument: bool = False
    # Unless has_default_argument is True then ignore argument_default
    argument_default: str | None = None
    attributes: list[Attribute] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Route:
    controller: str
    method_name: str
    return_type: str
    is_implicit_route: bool
    supported_http_verbs: list[str]
    accessible_at_urls: list[str]
    requires_authentication: bool
    authorisation_policies: list[str]
    inherited_authorisation_policies: list[str]
    arguments: list[Argument] = dataclasses.field(default_factory=list)
    attributes: list[Attribute] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class APIClass:
    class_name: str
    is_public_class: bool
    base_api_route: str
    base_api_route_raw: str
    requires_authentication: bool
    authorisation_policies: list[str]
    attributes: list[Attribute] = dataclasses.field(default_factory=list)
    routes: list[Route] = dataclasses.field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def transform_ast_to_routes(ast_api_class: ast.APIClass) -> APIClass:
    routes: list[Route] = []
    authorisation_policies = ast_api_class.get_authorization_polices()
    for method in ast_api_class.methods:
        if not method.is_public_method:
            # Google says routes must be public
            continue

        route = Route(
            attributes=method.attributes,
            return_type=method.return_type,
            method_name=method.method_name,
            arguments=method.arguments,
            is_implicit_route=(
                True
                if not method.has_route_attribute
                and not method.has_http_attribute
                and method.is_public_method
                else False
            ),
            accessible_at_urls=ast_api_class.get_method_routes(method),
            supported_http_verbs=ast_api_class.get_method_verbs(method),
            requires_authentication=method.requires_authentication(ast_api_class),
            authorisation_policies=method.get_authorization_polices(ast_api_class),
            inherited_authorisation_policies=authorisation_policies,
            controller=ast_api_class.class_name,
        )

        if route.is_implicit_route:
            # Need to set how it is route-able
            class_base = ast_api_class.get_class_route()
            if "[action]" in class_base:
                # Gets its own route
                route.accessible_at_urls.append(class_base.replace("[action]", method.method_name))

            else:
                # Has to share with other routes on the
                # base controller route level, shame
                route.accessible_at_urls.append(class_base)

        routes.append(route)

    return APIClass(
        attributes=ast_api_class.attributes,
        routes=routes,
        class_name=ast_api_class.class_name,
        is_public_class=ast_api_class.is_public_class,
        base_api_route=ast_api_class.get_class_route(),
        base_api_route_raw=ast_api_class.get_class_route(replace=False),
        requires_authentication=ast_api_class.requires_authentication,
        authorisation_policies=authorisation_policies,
    )
