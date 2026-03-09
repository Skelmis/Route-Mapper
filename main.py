import dataclasses
import io
import json
from ast import NodeVisitor
from pathlib import Path
from pprint import pprint

import code_ast
from code_ast import ASTVisitor, SourceCodeAST
from tree_sitter import Node


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
    argument_default: str | None = None


@dataclasses.dataclass
class Route:
    method_name: str
    is_public_method: bool
    return_type: str
    arguments: list[Argument] = dataclasses.field(default_factory=list)
    attributes: list[Attribute] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class APIClass:
    class_name: str
    is_public_class: bool
    attributes: list[Attribute] = dataclasses.field(default_factory=list)
    routes: list[Route] = dataclasses.field(default_factory=list)


# noinspection PyMethodMayBeStatic
class RMAstWalker(ASTVisitor):
    def __init__(self):
        self.api_class: APIClass | None = None

    def visit(self, node: Node):
        match node.type:
            case "class_declaration":
                self.api_class = self.build_class(node)

    def build_class(self, class_node: Node) -> APIClass:
        attached_attributes: list[Attribute] = []
        routes: list[Route] = []
        class_name: str = None
        public_class: bool = False
        for child in class_node.children:
            match child.type:
                case "attribute_list":
                    attached_attributes.append(self.extract_attributes(child))
                case "modifier":
                    public_class = child.children[0].type == "public"
                case "identifier":
                    class_name = child.text.decode()
                case "declaration_list":
                    for class_declaration in child.children:
                        match class_declaration.type:
                            case "method_declaration":
                                routes.append(
                                    self.build_class_methods(class_declaration)
                                )

        return APIClass(
            attributes=attached_attributes,
            routes=routes,
            class_name=class_name,
            is_public_class=public_class,
        )

    def build_class_methods(self, method_node: Node) -> Route:
        attributes: list[Attribute] = []
        arguments: list[Argument] = []
        public_method: bool | None = None
        return_type: str | None = None
        method_name: str = None

        for node in method_node.children:
            match node.type:
                case "attribute_list":
                    attributes.append(self.extract_attributes(node))
                case "modifier":
                    public_method = node.children[0].type == "public"
                case "generic_name":
                    return_type = node.text.decode()
                case "identifier":
                    method_name = node.text.decode()
                case "parameter_list":
                    for arg_node in node.named_children:
                        arguments.append(self.extract_argument(arg_node))

        return Route(
            attributes=attributes,
            return_type=return_type,
            is_public_method=public_method,
            method_name=method_name,
            arguments=arguments,
        )

    def extract_argument(self, argument_node: Node) -> Argument:
        argument_type = None
        argument_name = None
        argument_default: str | None = None
        is_nullable: bool = False
        for node in argument_node.named_children:
            match node.type:
                case "predefined_type":
                    # non-nullable
                    argument_type = node.text.decode()
                case "nullable_type":
                    assert (
                        node.children[0].type == "predefined_type"
                    ), "Expected to see the variable type"
                    is_nullable = True
                    argument_type = node.children[0].text.decode()
                case "identifier":
                    argument_name = node.text.decode()
                case "=":
                    # We work off expectations next is default
                    arg_default_node = node.next_named_sibling
                    argument_default = arg_default_node.text.decode()

        return Argument(
            argument_type=argument_type,
            argument_name=argument_name,
            argument_default=argument_default,
            is_nullable=is_nullable,
        )

    def extract_attributes(self, attribute_node: Node) -> Attribute:
        name = None
        args = None
        for child in attribute_node.children:
            if child.type != "attribute":
                continue

            for sub_child in child.children:
                match sub_child.type:
                    case "identifier":
                        name = sub_child.text
                    case "attribute_argument_list":
                        args = self.get_string_literal(sub_child, [])

        return Attribute(
            name=name.decode(), arguments=args if args is not None else None
        )

    def get_string_literal(self, node: Node, content: list[str]) -> list[str]:
        if len(node.named_children) == 0:
            content.append(node.text.decode())
            return content

        for child in node.named_children:
            self.get_string_literal(child, content)

        return content


def main():
    base_path: Path = Path(
        "/home/skelmis/tmp/chsarp_ast/WebApplication1/WebApplication1/Controllers"
    )
    for file in base_path.rglob("**/*Controller.cs"):
        file_content = file.read_text()
        source_ast: SourceCodeAST = code_ast.ast(file_content, lang="c_sharp")
        rm_ast_walker = RMAstWalker()
        rm_ast_walker.walk(source_ast.root_node())
        pprint(rm_ast_walker.api_class)
        with open("ast_out.json", "w") as f:
            f.write(json.dumps(dataclasses.asdict(rm_ast_walker.api_class), indent=4))

        # print(count_visitor.node_types)


if __name__ == "__main__":
    main()
