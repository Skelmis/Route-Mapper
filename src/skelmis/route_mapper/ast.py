from __future__ import annotations

import dataclasses
import re
from modulefinder import replacePackageMap
from typing import Any

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
    has_default_argument: bool = False
    # Unless has_default_argument is True then ignore argument_default
    argument_default: str | None = None
    attributes: list[Attribute] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Method:
    method_name: str
    is_public_method: bool
    return_type: str
    arguments: list[Argument] = dataclasses.field(default_factory=list)
    attributes: list[Attribute] = dataclasses.field(default_factory=list)

    @property
    def has_route_attribute(self) -> bool:
        for attr in self.attributes:
            if attr.name == "Route":
                return True
        return False

    @property
    def has_http_attribute(self) -> bool:
        for attr in self.attributes:
            if attr.name.startswith("Http"):
                return True
        return False

    def requires_authentication(self, parent_class: APIClass) -> bool:
        if parent_class.has_allow_anonymous_attribute or self.has_allow_anonymous_attribute:
            # This takes precedence
            return False

        return parent_class.has_authorize_attribute or self.has_authorize_attribute

    @property
    def has_allow_anonymous_attribute(self) -> bool:
        # Special attribute to bypass auth
        for attr in self.attributes:
            if attr.name == "AllowAnonymous":
                return True

        return False

    @property
    def has_authorize_attribute(self) -> bool:
        # Special attribute to bypass auth
        for attr in self.attributes:
            if attr.name == "Authorize":
                return True

        return False

    def get_authorization_polices(self, parent_class: APIClass) -> list[str]:
        if not self.requires_authentication(parent_class):
            return []

        policies: list[str] = []
        for attr in self.attributes:
            if attr.name == "Authorize" and attr.arguments is not None:
                policies.append(attr.arguments[0])

        return policies


@dataclasses.dataclass
class APIClass:
    class_name: str
    is_public_class: bool
    attributes: list[Attribute] = dataclasses.field(default_factory=list)
    methods: list[Method] = dataclasses.field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @property
    def cleaned_class_name(self) -> str:
        return self.class_name.removesuffix("Controller")

    @property
    def area(self) -> str:
        for attr in self.attributes:
            if attr.name == "Area":
                return attr.arguments[0]

        return ""

    @property
    def requires_authentication(self) -> bool:
        if self.has_allow_anonymous_attribute:
            # This takes precedence
            return False

        return self.has_authorize_attribute

    @property
    def has_allow_anonymous_attribute(self) -> bool:
        # Special attribute to bypass auth
        for attr in self.attributes:
            if attr.name == "AllowAnonymous":
                return True

        return False

    @property
    def has_authorize_attribute(self) -> bool:
        # Special attribute to bypass auth
        for attr in self.attributes:
            if attr.name == "Authorize":
                return True

        return False

    def get_authorization_polices(self) -> list[str]:
        if self.has_allow_anonymous_attribute:
            return []

        policies: list[str] = []
        for attr in self.attributes:
            if attr.name == "Authorize" and attr.arguments is not None:
                policies.append(attr.arguments[0])

        return policies

    def get_class_route(self, *, replace: bool = True) -> str:
        url = None
        for attr in self.attributes:
            if attr.name == "Route":
                url = attr.arguments[0]
                if replace:
                    url = url.replace("[controller]", self.cleaned_class_name).replace(
                        "[area]", self.area
                    )

        assert url is not None, 'Controllers must have an attribute "Route"'
        return url

    def get_method_verbs(self, method: Method) -> list[str]:
        verbs: list[str] = []
        for attr in method.attributes:
            if not attr.name.startswith("Http"):
                continue

            verbs.append(attr.name.removeprefix("Http").upper())

        return verbs

    def get_method_routes(self, method: Method) -> list[str]:
        routes: list[str] = []
        base_route: str | None = None
        class_base = self.get_class_route()
        for attr in method.attributes:
            if attr.name != "Route" and not attr.name.startswith("Http"):
                continue

            if attr.name.startswith("Http"):
                if attr.arguments is None:
                    # [HttpGet]
                    if "[action]" in class_base:
                        # [Route("[controller]/[action]")]
                        base_route = class_base.replace("[action]", method.method_name)

                    continue

                method_route = attr.arguments[0]
                if re.match(r"^ *[a-zA-Z0-9]+ ?=", method_route):
                    # Argument, not route
                    # HttpGet(Name = "GetWeatherForecast")
                    base_route = class_base.replace("[action]", method.method_name)
                    continue

            else:
                method_route = attr.arguments[0]

            method_route = (
                method_route.replace(
                    "[controller]",
                    self.cleaned_class_name,
                )
                .replace("[area]", self.area)
                .replace("[action]", method.method_name)
            )
            if method_route.startswith("/"):
                routes.append(method_route)
            else:
                routes.append(
                    "/".join([class_base.replace("[action]", method.method_name), method_route])
                )

        if not routes and base_route is not None:
            routes.append(base_route)

        return routes


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
        methods: list[Method] = []
        class_name: str | None = None
        public_class: bool = False
        for child in class_node.children:
            match child.type:
                case "attribute_list":
                    attached_attributes.extend(self.extract_attributes(child))
                case "modifier":
                    public_class = child.children[0].type == "public"
                case "identifier":
                    class_name = child.text.decode()
                case "declaration_list":
                    for class_declaration in child.children:
                        match class_declaration.type:
                            case "method_declaration":
                                methods.append(self.build_class_methods(class_declaration))

        return APIClass(
            attributes=attached_attributes,
            methods=methods,
            class_name=class_name,
            is_public_class=public_class,
        )

    def build_class_methods(self, method_node: Node) -> Method:
        attributes: list[Attribute] = []
        arguments: list[Argument] = []
        method_identifiers: list[str] = []
        return_type: str | None = None
        method_name: str | None = None

        for node in method_node.children:
            match node.type:
                case "attribute_list":
                    attributes.extend(self.extract_attributes(node))
                case "modifier":
                    method_identifiers.append(node.children[0].text.decode())
                case "generic_name":
                    return_type = node.text.decode()
                case "identifier":
                    method_name = node.text.decode()
                case "parameter_list":
                    for arg_node in node.named_children:
                        arguments.append(self.extract_argument(arg_node))

        return Method(
            attributes=attributes,
            return_type=return_type,
            is_public_method="public" in method_identifiers,
            method_name=method_name,
            arguments=arguments,
        )

    def extract_argument(self, argument_node: Node) -> Argument:
        argument_type = None
        argument_name = None
        argument_default: str | None = None
        has_default_argument: bool = False
        is_nullable: bool = False
        attributes: list[Attribute] = []
        for node in argument_node.children:
            match node.type:
                case "attribute_list":
                    attributes.extend(self.extract_attributes(node))
                case "predefined_type":
                    # non-nullable
                    argument_type = node.text.decode()
                case "nullable_type":
                    assert node.children[0].type in (
                        "predefined_type",
                        "identifier",
                    ), "Expected to see the variable type"
                    is_nullable = True
                    argument_type = node.children[0].text.decode()
                case "identifier":
                    argument_name = node.text.decode()
                case "=":
                    # We work off expectations next is default
                    arg_default_node = node.next_named_sibling
                    argument_default = arg_default_node.text.decode()
                    has_default_argument = True

        return Argument(
            argument_type=argument_type,
            argument_name=argument_name,
            argument_default=argument_default,
            has_default_argument=has_default_argument,
            is_nullable=is_nullable,
            attributes=attributes,
        )

    def extract_attributes(self, attribute_node: Node) -> list[Attribute]:
        attributes: list[Attribute] = []
        for attribute in attribute_node.named_children:
            if attribute.type != "attribute":
                continue

            name = None
            args = None
            for child in attribute.children:
                match child.type:
                    case "identifier":
                        name = child.text
                    case "attribute_argument_list":
                        args = self.get_string_literal(child, [])

            attributes.append(
                Attribute(name=name.decode(), arguments=args if args is not None else None)
            )
        return attributes

    def get_string_literal(self, node: Node, content: list[str]) -> list[str]:
        if len(node.named_children) == 0:
            content.append(node.text.decode())
            return content

        elif (
            len(node.children) == 3
            and node.children[0].type == "identifier"
            and node.children[1].type == "="
        ):
            # ErrorMessage = "Expected 1-10"
            new_content = []
            self.get_string_literal(node.named_children[0], new_content)
            self.get_string_literal(node.named_children[1], new_content)
            content.append(" = ".join(new_content))
            return content

        for child in node.named_children:
            self.get_string_literal(child, content)

        return content


def file_to_api_class(file_content: str) -> APIClass:
    source_ast: SourceCodeAST = code_ast.ast(file_content, lang="c_sharp")
    rm_ast_walker = RMAstWalker()
    rm_ast_walker.walk(source_ast.root_node())
    return rm_ast_walker.api_class
