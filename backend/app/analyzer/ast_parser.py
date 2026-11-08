import os

import tree_sitter_python
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

from app.schemas.code_context import EnclosingScope, ImportStatement, ScopeType

# Initialize Tree-sitter Languages and Parsers
PY_LANGUAGE = Language(tree_sitter_python.language())
TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())

_parsers = {
    "python": Parser(PY_LANGUAGE),
    "typescript": Parser(TS_LANGUAGE),
    "tsx": Parser(TSX_LANGUAGE),
    "javascript": Parser(TSX_LANGUAGE),  # TSX grammar is a superset of JS/JSX
}


class TreeSitterASTParser:
    """
    AST analysis engine using Tree-sitter for Python and TypeScript/JavaScript.
    Extracts enclosing scopes (classes, functions, methods), decorators, parameters,
    and imports, and locates enclosing scopes for given line numbers.
    """

    @staticmethod
    def detect_language(file_path: str) -> str:
        """Detect language identifier from file extension."""
        _, ext = os.path.splitext(file_path.lower())
        if ext == ".py":
            return "python"
        elif ext == ".ts":
            return "typescript"
        elif ext in (".tsx", ".jsx"):
            return "tsx"
        elif ext in (".js", ".mjs", ".cjs"):
            return "javascript"
        return "unknown"

    @classmethod
    def parse_code(cls, code: str, language: str) -> Node | None:
        """Parse source code string into a Tree-sitter root Node."""
        parser = _parsers.get(language)
        if not parser:
            return None
        code_bytes = code.encode("utf-8")
        tree = parser.parse(code_bytes)
        return tree.root_node

    @classmethod
    def extract_scopes(cls, code: str, language: str) -> list[EnclosingScope]:
        """Extract all function, method, class, and interface scopes from source code."""
        root_node = cls.parse_code(code, language)
        if not root_node:
            return []

        code_bytes = code.encode("utf-8")
        scopes: list[EnclosingScope] = []

        if language == "python":
            cls._extract_python_scopes(root_node, code_bytes, scopes)
        elif language in ("typescript", "tsx", "javascript"):
            cls._extract_typescript_scopes(root_node, code_bytes, scopes)

        return scopes

    @classmethod
    def extract_imports(cls, code: str, language: str) -> list[ImportStatement]:
        """Extract all import statements and imported symbols."""
        root_node = cls.parse_code(code, language)
        if not root_node:
            return []

        code_bytes = code.encode("utf-8")
        imports: list[ImportStatement] = []

        if language == "python":
            cls._extract_python_imports(root_node, code_bytes, imports)
        elif language in ("typescript", "tsx", "javascript"):
            cls._extract_typescript_imports(root_node, code_bytes, imports)

        return imports

    @classmethod
    def find_enclosing_scopes_for_lines(
        cls, scopes: list[EnclosingScope], line_numbers: list[int]
    ) -> tuple[EnclosingScope | None, EnclosingScope | None]:
        """
        Given a list of scopes and 1-based line numbers, finds:
        1. Innermost function/method scope enclosing the lines.
        2. Innermost class/interface scope enclosing the lines.
        """
        if not line_numbers:
            return None, None

        min_line = min(line_numbers)
        max_line = max(line_numbers)

        candidate_functions: list[EnclosingScope] = []
        candidate_classes: list[EnclosingScope] = []

        for scope in scopes:
            # Check if scope spans the lines
            if scope.start_line <= min_line and scope.end_line >= max_line:
                if scope.scope_type in ("function", "method", "arrow_function"):
                    candidate_functions.append(scope)
                elif scope.scope_type in ("class", "interface"):
                    candidate_classes.append(scope)

        # Pick the most specific (smallest line span) candidates
        innermost_function = (
            min(candidate_functions, key=lambda s: s.end_line - s.start_line)
            if candidate_functions
            else None
        )
        innermost_class = (
            min(candidate_classes, key=lambda s: s.end_line - s.start_line)
            if candidate_classes
            else None
        )

        return innermost_function, innermost_class
    
    @classmethod
    def _extract_python_scopes(
        cls,
        node: Node,
        code_bytes: bytes,
        scopes: list[EnclosingScope],
        parent_class: str | None = None,
        pending_decorators: list[str] | None = None,
        decorated_start_line: int | None = None,
    ) -> None:
        decorators = pending_decorators or []

        if node.type == "decorated_definition":
            # Extract decorators
            found_decorators = []
            def_node = None
            for child in node.children:
                if child.type == "decorator":
                    found_decorators.append(child.text.decode("utf-8").strip())
                elif child.type in ("function_definition", "class_definition"):
                    def_node = child

            if def_node:
                cls._extract_python_scopes(
                    def_node,
                    code_bytes,
                    scopes,
                    parent_class=parent_class,
                    pending_decorators=found_decorators,
                    decorated_start_line=node.start_point[0] + 1,
                )
            return

        if node.type in ("function_definition", "async_function_definition"):
            name_node = node.child_by_field_name("name")
            fn_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"
            scope_type: ScopeType = "method" if parent_class else "function"

            # Parameters
            params: list[str] = []
            params_node = node.child_by_field_name("parameters")
            if params_node:
                for param in params_node.children:
                    if param.type in (
                        "identifier",
                        "typed_parameter",
                        "default_parameter",
                        "typed_default_parameter",
                    ):
                        params.append(param.text.decode("utf-8").strip())

            # Return type
            return_type = None
            return_node = node.child_by_field_name("return_type")
            if return_node:
                return_type = return_node.text.decode("utf-8").strip()

            # Docstring
            docstring = cls._get_python_docstring(node)

            start_line = decorated_start_line or (node.start_point[0] + 1)
            scope = EnclosingScope(
                scope_type=scope_type,
                name=fn_name,
                start_line=start_line,
                end_line=node.end_point[0] + 1,
                parameters=params,
                return_type=return_type,
                decorators=decorators,
                docstring=docstring,
            )
            scopes.append(scope)

        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            class_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            docstring = cls._get_python_docstring(node)

            start_line = decorated_start_line or (node.start_point[0] + 1)
            scope = EnclosingScope(
                scope_type="class",
                name=class_name,
                start_line=start_line,
                end_line=node.end_point[0] + 1,
                decorators=decorators,
                docstring=docstring,
            )
            scopes.append(scope)

            # Traverse body with parent_class set
            body = node.child_by_field_name("body")
            if body:
                for child in body.children:
                    cls._extract_python_scopes(child, code_bytes, scopes, parent_class=class_name)
            return

        # Recurse children
        for child in node.children:
            cls._extract_python_scopes(child, code_bytes, scopes, parent_class=parent_class)

    @staticmethod
    def _get_python_docstring(node: Node) -> str | None:
        body = node.child_by_field_name("body")
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement" and first_stmt.children:
                expr = first_stmt.children[0]
                if expr.type == "string":
                    raw = expr.text.decode("utf-8").strip()
                    # Strip triple quotes
                    if raw.startswith(('"""', "'''")) and raw.endswith(('"""', "'''")):
                        return raw[3:-3].strip()
                    elif raw.startswith(('"', "'")) and raw.endswith(('"', "'")):
                        return raw[1:-1].strip()
                    return raw
        return None

    @classmethod
    def _extract_python_imports(
        cls, node: Node, code_bytes: bytes, imports: list[ImportStatement]
    ) -> None:
        if node.type == "import_statement":
            # e.g., import os, sys as system
            line_no = node.start_point[0] + 1
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(
                        ImportStatement(
                            module=child.text.decode("utf-8"),
                            imported_symbols=[],
                            is_wildcard=False,
                            line_number=line_no,
                        )
                    )
                elif child.type == "aliased_import":
                    name = child.child_by_field_name("name")
                    alias = child.child_by_field_name("alias")
                    imports.append(
                        ImportStatement(
                            module=name.text.decode("utf-8") if name else "",
                            imported_symbols=[],
                            is_wildcard=False,
                            alias=alias.text.decode("utf-8") if alias else None,
                            line_number=line_no,
                        )
                    )

        elif node.type == "import_from_statement":
            # e.g., from fastapi import FastAPI, Depends or from math import *
            line_no = node.start_point[0] + 1
            module_name = ""
            module_node = node.child_by_field_name("module_name")
            if module_node:
                module_name = module_node.text.decode("utf-8")

            symbols: list[str] = []
            is_wildcard = False

            for child in node.children:
                if child.type == "wildcard_import":
                    is_wildcard = True
                elif child.type == "dotted_name" and child != module_node:
                    symbols.append(child.text.decode("utf-8"))
                elif child.type == "aliased_import":
                    name = child.child_by_field_name("name")
                    if name:
                        symbols.append(name.text.decode("utf-8"))

            imports.append(
                ImportStatement(
                    module=module_name,
                    imported_symbols=symbols,
                    is_wildcard=is_wildcard,
                    line_number=line_no,
                )
            )

        for child in node.children:
            cls._extract_python_imports(child, code_bytes, imports)

    @classmethod
    def _extract_typescript_scopes(
        cls,
        node: Node,
        code_bytes: bytes,
        scopes: list[EnclosingScope],
        parent_class: str | None = None,
    ) -> None:
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            fn_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            params = cls._get_ts_parameters(node)
            return_type = cls._get_ts_return_type(node)

            scopes.append(
                EnclosingScope(
                    scope_type="function",
                    name=fn_name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    parameters=params,
                    return_type=return_type,
                )
            )

        elif node.type == "method_definition":
            name_node = node.child_by_field_name("name")
            method_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            params = cls._get_ts_parameters(node)
            return_type = cls._get_ts_return_type(node)

            scopes.append(
                EnclosingScope(
                    scope_type="method",
                    name=f"{parent_class}.{method_name}" if parent_class else method_name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    parameters=params,
                    return_type=return_type,
                )
            )

        elif node.type in ("class_declaration", "abstract_class_declaration"):
            name_node = node.child_by_field_name("name")
            class_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            scopes.append(
                EnclosingScope(
                    scope_type="class",
                    name=class_name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )
            )

            body = node.child_by_field_name("body")
            if body:
                for child in body.children:
                    cls._extract_typescript_scopes(
                        child, code_bytes, scopes, parent_class=class_name
                    )
            return

        elif node.type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            interface_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            scopes.append(
                EnclosingScope(
                    scope_type="interface",
                    name=interface_name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )
            )

        elif node.type in ("lexical_declaration", "variable_declaration"):
            # Check for arrow functions assigned to const/let
            for declarator in node.children:
                if declarator.type == "variable_declarator":
                    name_child = declarator.child_by_field_name("name")
                    val_child = declarator.child_by_field_name("value")
                    if val_child and val_child.type == "arrow_function" and name_child:
                        fn_name = name_child.text.decode("utf-8")
                        params = cls._get_ts_parameters(val_child)
                        return_type = cls._get_ts_return_type(val_child)

                        scopes.append(
                            EnclosingScope(
                                scope_type="arrow_function",
                                name=fn_name,
                                start_line=declarator.start_point[0] + 1,
                                end_line=declarator.end_point[0] + 1,
                                parameters=params,
                                return_type=return_type,
                            )
                        )

        for child in node.children:
            cls._extract_typescript_scopes(child, code_bytes, scopes, parent_class=parent_class)

    @staticmethod
    def _get_ts_parameters(node: Node) -> list[str]:
        params: list[str] = []
        params_node = node.child_by_field_name("parameters")
        if params_node:
            for p in params_node.children:
                if p.type in (
                    "required_parameter",
                    "optional_parameter",
                    "identifier",
                    "formal_parameters",
                ):
                    params.append(p.text.decode("utf-8").strip())
        return params

    @staticmethod
    def _get_ts_return_type(node: Node) -> str | None:
        return_node = node.child_by_field_name("return_type")
        if return_node:
            raw = return_node.text.decode("utf-8").strip()
            if raw.startswith(":"):
                return raw[1:].strip()
            return raw
        return None

    @classmethod
    def _extract_typescript_imports(
        cls, node: Node, code_bytes: bytes, imports: list[ImportStatement]
    ) -> None:
        if node.type == "import_statement":
            line_no = node.start_point[0] + 1
            source_node = node.child_by_field_name("source")
            module_name = ""
            if source_node:
                raw_source = source_node.text.decode("utf-8").strip()
                module_name = raw_source.strip("'\"")

            symbols: list[str] = []
            is_wildcard = False

            # Inspect import clause
            for child in node.children:
                if child.type == "import_clause":
                    for clause_child in child.children:
                        if clause_child.type == "identifier":
                            # Default import (e.g. import React from 'react')
                            symbols.append(clause_child.text.decode("utf-8"))
                        elif clause_child.type == "named_imports":
                            for specifier in clause_child.children:
                                if specifier.type == "import_specifier":
                                    name = specifier.child_by_field_name("name")
                                    if name:
                                        symbols.append(name.text.decode("utf-8"))
                        elif clause_child.type == "namespace_import":
                            is_wildcard = True
                            alias = clause_child.child_by_field_name("name")
                            if alias:
                                symbols.append(alias.text.decode("utf-8"))

            imports.append(
                ImportStatement(
                    module=module_name,
                    imported_symbols=symbols,
                    is_wildcard=is_wildcard,
                    line_number=line_no,
                )
            )

        for child in node.children:
            cls._extract_typescript_imports(child, code_bytes, imports)
