import dataclasses
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
