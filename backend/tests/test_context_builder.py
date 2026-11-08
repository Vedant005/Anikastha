from app.analyzer.context_builder import RepositoryContextBuilder
from app.github.diff_parser import DiffParser

PYTHON_CODE = """import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: int):
    # Retrieve user
    return {"user_id": user_id}

class AccountManager:
    def close_account(self, account_id: str):
        print(f"Closing {account_id}")
        return True
"""

SAMPLE_DIFF = """diff --git a/app/users.py b/app/users.py
index 1111111..2222222 100644
--- a/app/users.py
+++ b/app/users.py
@@ -7,3 +7,4 @@ def get_user(user_id: int):
     # Retrieve user
+    if user_id <= 0: return None
     return {"user_id": user_id}
"""


def test_build_file_context_with_ast():
    files = DiffParser.parse_diff(SAMPLE_DIFF)
    assert len(files) == 1
    diff_file = files[0]

    ctx = RepositoryContextBuilder.build_file_context(
        diff_file=diff_file,
        file_content=PYTHON_CODE,
    )

    assert ctx.file_path == "app/users.py"
    assert ctx.language == "python"
    assert len(ctx.hunk_contexts) == 1

    hunk_ctx = ctx.hunk_contexts[0]
    # Enclosing scope should be get_user
    assert hunk_ctx.enclosing_scope is not None
    assert hunk_ctx.enclosing_scope.name == "get_user"
    assert hunk_ctx.enclosing_scope.scope_type == "function"
    assert hunk_ctx.enclosing_class is None

    # Surrounding code should be populated
    assert hunk_ctx.surrounding_code is not None
    assert "def get_user" in hunk_ctx.surrounding_code


def test_build_file_context_without_content():
    files = DiffParser.parse_diff(SAMPLE_DIFF)
    diff_file = files[0]

    ctx = RepositoryContextBuilder.build_file_context(
        diff_file=diff_file,
        file_content=None,
    )

    assert ctx.language == "python"
    assert len(ctx.hunk_contexts) == 1
    assert ctx.hunk_contexts[0].enclosing_scope is None
    assert ctx.hunk_contexts[0].surrounding_code is None
