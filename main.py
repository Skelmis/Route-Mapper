import json
from pathlib import Path

from skelmis import route_mapper
from skelmis.route_mapper import rules


def main():
    base_path: Path = Path(
        "/home/skelmis/tmp/chsarp_ast/WebApplication1/WebApplication1/Controllers"
    )
    api_classes: list[route_mapper.transform.APIClass] = []
    output_folder: Path = Path("output")
    controllers_folder = output_folder / "controllers"
    rules_folder = output_folder / "rules"
    controllers_folder.mkdir(parents=True, exist_ok=True)
    rules_folder.mkdir(parents=True, exist_ok=True)

    for file in base_path.rglob("**/*Controller.cs"):
        file_content = file.read_text()
        api_class: route_mapper.ast.APIClass = route_mapper.file_to_api_class(file_content)
        route_class: route_mapper.transform.APIClass = route_mapper.transform_ast_to_routes(
            api_class
        )
        api_classes.append(route_class)
        with open(output_folder / "controllers" / f"{file.name}.json", "w") as f:
            f.write(json.dumps(route_class.as_dict(), indent=4))

    implicit_routes: rules.ImplicitRoutes = rules.get_implicit_routes(*api_classes)
    with open(output_folder / "rules" / f"implicit_routes.json", "w") as f:
        f.write(json.dumps(implicit_routes.as_dict(), indent=4))

    policy_grouped_routes: rules.RoutesPerAuthorisationPolicy = rules.get_routes_group_by_authz(*api_classes)
    with open(output_folder / "rules" / f"policy_grouped_routes.json", "w") as f:
        f.write(json.dumps(policy_grouped_routes.as_dict(), indent=4))

    print("Done")


if __name__ == "__main__":
    main()
