import json
from pathlib import Path

from skelmis import route_mapper


def main():
    base_path: Path = Path(
        "/home/skelmis/tmp/chsarp_ast/WebApplication1/WebApplication1/Controllers"
    )
    for file in base_path.rglob("**/*Controller.cs"):
        file_content = file.read_text()
        api_class: route_mapper.ast.APIClass = route_mapper.file_to_api_class(file_content)
        with open("ast_out.json", "w") as f:
            f.write(json.dumps(api_class.as_dict(), indent=4))

    print("Done")


if __name__ == "__main__":
    main()
