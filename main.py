import json
from pathlib import Path

from skelmis import route_mapper


def main():
    base_path: Path = Path(
        "/home/skelmis/tmp/chsarp_ast/WebApplication1/WebApplication1/Controllers"
    )
    output_folder: Path = Path("output")
    output_folder.mkdir(parents=True, exist_ok=True)
    for file in base_path.rglob("**/*Controller.cs"):
        file_content = file.read_text()
        api_class: route_mapper.ast.APIClass = route_mapper.file_to_api_class(file_content)
        route_class: route_mapper.transform.APIClass = route_mapper.transform_ast_to_routes(
            api_class
        )
        with open(output_folder / f"{file.name}.json", "w") as f:
            f.write(json.dumps(route_class.as_dict(), indent=4))

    print("Done")


if __name__ == "__main__":
    main()
