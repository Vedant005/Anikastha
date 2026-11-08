from typing import Literal

from pydantic import BaseModel, Field

DiffLineType = Literal["add", "delete", "context"]
FileStatus = Literal["added", "modified", "deleted", "renamed"]
ScopeType = Literal["function", "method", "class", "module", "arrow_function", "interface"]


class DiffLine(BaseModel):
    type: DiffLineType
    content: str
    old_line_number: int | None = None
    new_line_number: int | None = None
    is_commentable: bool = False


class DiffHunk(BaseModel):
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    lines: list[DiffLine] = Field(default_factory=list)
    valid_new_lines: list[int] = Field(default_factory=list)


class DiffFile(BaseModel):
    old_path: str
    new_path: str
    status: FileStatus
    hunks: list[DiffHunk] = Field(default_factory=list)
    is_binary: bool = False
    additions_count: int = 0
    deletions_count: int = 0


class EnclosingScope(BaseModel):
    scope_type: ScopeType
    name: str
    start_line: int  # 1-based
    end_line: int  # 1-based
    parameters: list[str] = Field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = Field(default_factory=list)
    docstring: str | None = None


class ImportStatement(BaseModel):
    module: str
    imported_symbols: list[str] = Field(default_factory=list)
    is_wildcard: bool = False
    alias: str | None = None
    line_number: int


class HunkContext(BaseModel):
    hunk: DiffHunk
    enclosing_scope: EnclosingScope | None = None
    enclosing_class: EnclosingScope | None = None
    relevant_imports: list[ImportStatement] = Field(default_factory=list)
    surrounding_code: str | None = None


class FileAnalysisContext(BaseModel):
    file_path: str
    language: str  # python, typescript, javascript, unknown
    diff_file: DiffFile
    hunk_contexts: list[HunkContext] = Field(default_factory=list)
    all_imports: list[ImportStatement] = Field(default_factory=list)
    full_content: str | None = None
