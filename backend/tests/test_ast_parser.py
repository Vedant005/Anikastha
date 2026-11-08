from app.analyzer.ast_parser import TreeSitterASTParser

PYTHON_SAMPLE = '''
import os
import sys as system
from fastapi import FastAPI, Depends
from math import *

@router.post("/items")
async def create_item(name: str, price: float) -> dict:
    """Create a new store item."""
    return {"name": name, "price": price}

class OrderService:
    """Handles order processing."""
    
    @transactional
    def process_order(self, order_id: int):
        total = 100
        return total
'''

TYPESCRIPT_SAMPLE = """
import React, { useState, useEffect } from 'react';
import * as path from 'path';

export interface UserProps {
    id: string;
    email: string;
}

export class UserService {
    getUser(id: string): UserProps {
        return { id, email: "user@example.com" };
    }
}

export function formatUser(user: UserProps): string {
    return `${user.id}: ${user.email}`;
}

export const calculateDiscount = (total: number): number => {
    return total * 0.1;
};
"""


def test_language_detection():
    assert TreeSitterASTParser.detect_language("main.py") == "python"
    assert TreeSitterASTParser.detect_language("src/index.ts") == "typescript"
    assert TreeSitterASTParser.detect_language("components/Button.tsx") == "tsx"
    assert TreeSitterASTParser.detect_language("utils.js") == "javascript"
    assert TreeSitterASTParser.detect_language("styles.css") == "unknown"


def test_python_ast_scopes():
    scopes = TreeSitterASTParser.extract_scopes(PYTHON_SAMPLE, "python")
    scope_names = {s.name: s for s in scopes}

    # Verify function
    assert "create_item" in scope_names
    fn = scope_names["create_item"]
    assert fn.scope_type == "function"
    assert "name: str" in fn.parameters[0]
    assert "dict" in (fn.return_type or "")
    assert "@router.post" in fn.decorators[0]
    assert fn.docstring == "Create a new store item."

    # Verify class
    assert "OrderService" in scope_names
    cls_scope = scope_names["OrderService"]
    assert cls_scope.scope_type == "class"
    assert cls_scope.docstring == "Handles order processing."

    # Verify method
    assert "process_order" in scope_names
    method = scope_names["process_order"]
    assert method.scope_type == "method"
    assert "@transactional" in method.decorators[0]


def test_python_ast_imports():
    imports = TreeSitterASTParser.extract_imports(PYTHON_SAMPLE, "python")
    modules = {i.module: i for i in imports}

    assert "os" in modules
    assert "sys" in modules
    assert modules["sys"].alias == "system"

    assert "fastapi" in modules
    assert "FastAPI" in modules["fastapi"].imported_symbols
    assert "Depends" in modules["fastapi"].imported_symbols

    assert "math" in modules
    assert modules["math"].is_wildcard is True


def test_typescript_ast_scopes():
    scopes = TreeSitterASTParser.extract_scopes(TYPESCRIPT_SAMPLE, "typescript")
    scope_names = {s.name: s for s in scopes}

    assert "UserProps" in scope_names
    assert scope_names["UserProps"].scope_type == "interface"

    assert "UserService" in scope_names
    assert scope_names["UserService"].scope_type == "class"

    assert "UserService.getUser" in scope_names
    assert scope_names["UserService.getUser"].scope_type == "method"
    assert "UserProps" in (scope_names["UserService.getUser"].return_type or "")

    assert "formatUser" in scope_names
    assert scope_names["formatUser"].scope_type == "function"

    assert "calculateDiscount" in scope_names
    assert scope_names["calculateDiscount"].scope_type == "arrow_function"


def test_typescript_ast_imports():
    imports = TreeSitterASTParser.extract_imports(TYPESCRIPT_SAMPLE, "typescript")
    modules = {i.module: i for i in imports}

    assert "react" in modules
    assert "React" in modules["react"].imported_symbols
    assert "useState" in modules["react"].imported_symbols
    assert "useEffect" in modules["react"].imported_symbols

    assert "path" in modules
    assert modules["path"].is_wildcard is True


def test_find_enclosing_scopes_for_lines():
    scopes = TreeSitterASTParser.extract_scopes(PYTHON_SAMPLE, "python")

    # Lines 8-10 are inside create_item
    fn, cls_scope = TreeSitterASTParser.find_enclosing_scopes_for_lines(scopes, [8, 10])
    assert fn is not None
    assert fn.name == "create_item"
    assert cls_scope is None

    # Line 18 is inside process_order which is inside OrderService
    method, cls_scope2 = TreeSitterASTParser.find_enclosing_scopes_for_lines(scopes, [18])
    assert method is not None
    assert method.name == "process_order"
    assert cls_scope2 is not None
    assert cls_scope2.name == "OrderService"

    # Line outside any function (e.g. imports at line 2)
    fn3, cls3 = TreeSitterASTParser.find_enclosing_scopes_for_lines(scopes, [2])
    assert fn3 is None
    assert cls3 is None
