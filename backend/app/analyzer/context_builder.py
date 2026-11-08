from app.analyzer.ast_parser import TreeSitterASTParser
from app.schemas.code_context import (
    DiffFile,
    DiffHunk,
    FileAnalysisContext,
    HunkContext,
    ImportStatement,
)


class RepositoryContextBuilder:
    """
    Assembles rich syntactic and semantic context by uniting Git Diff Hunks
    with Tree-sitter AST scopes, enclosing functions/classes, and module imports.
    """

    @classmethod
    def build_file_context(
        cls,
        diff_file: DiffFile,
        file_content: str | None = None,
    ) -> FileAnalysisContext:
        """
        Builds a FileAnalysisContext for a modified file, linking each hunk to its
        enclosing function, class, imports, and surrounding code.
        """
        language = TreeSitterASTParser.detect_language(diff_file.new_path)
        all_imports: list[ImportStatement] = []
        hunk_contexts: list[HunkContext] = []

        if file_content and language != "unknown":
            scopes = TreeSitterASTParser.extract_scopes(file_content, language)
            all_imports = TreeSitterASTParser.extract_imports(file_content, language)
            file_lines = file_content.splitlines()

            for hunk in diff_file.hunks:
                hunk_ctx = cls._build_hunk_context(
                    hunk=hunk,
                    scopes=scopes,
                    all_imports=all_imports,
                    file_lines=file_lines,
                )
                hunk_contexts.append(hunk_ctx)
        else:
            # Fallback for deleted, binary, or unsupported languages
            for hunk in diff_file.hunks:
                hunk_contexts.append(
                    HunkContext(
                        hunk=hunk,
                        enclosing_scope=None,
                        enclosing_class=None,
                        relevant_imports=[],
                        surrounding_code=None,
                    )
                )

        return FileAnalysisContext(
            file_path=diff_file.new_path,
            language=language,
            diff_file=diff_file,
            hunk_contexts=hunk_contexts,
            all_imports=all_imports,
            full_content=file_content,
        )

    @classmethod
    def _build_hunk_context(
        cls,
        hunk: DiffHunk,
        scopes: list,
        all_imports: list[ImportStatement],
        file_lines: list[str],
    ) -> HunkContext:
        # Target lines that were added or modified
        added_lines = [
            line.new_line_number
            for line in hunk.lines
            if line.type == "add" and line.new_line_number is not None
        ]

        # If no additions, fall back to valid hunk new lines or hunk range
        target_lines = added_lines or hunk.valid_new_lines or [hunk.new_start]

        enclosing_fn, enclosing_class = TreeSitterASTParser.find_enclosing_scopes_for_lines(
            scopes, target_lines
        )

        # Surrounding code: extract enclosing scope body or 5 lines of context
        surrounding_code = None
        if enclosing_fn:
            start_idx = max(0, enclosing_fn.start_line - 1)
            end_idx = min(len(file_lines), enclosing_fn.end_line)
            surrounding_code = "\n".join(file_lines[start_idx:end_idx])
        elif enclosing_class:
            start_idx = max(0, enclosing_class.start_line - 1)
            end_idx = min(len(file_lines), enclosing_class.end_line)
            surrounding_code = "\n".join(file_lines[start_idx:end_idx])
        else:
            # Window of 5 lines before and after hunk
            start_idx = max(0, hunk.new_start - 6)
            end_idx = min(len(file_lines), hunk.new_start + hunk.new_lines + 5)
            surrounding_code = "\n".join(file_lines[start_idx:end_idx])

        # Filter relevant imports: imports whose symbols appear in hunk text or enclosing code
        hunk_text = "\n".join(line.content for line in hunk.lines)
        relevant_imports = [
            imp
            for imp in all_imports
            if imp.module in hunk_text or any(sym in hunk_text for sym in imp.imported_symbols)
        ]

        return HunkContext(
            hunk=hunk,
            enclosing_scope=enclosing_fn,
            enclosing_class=enclosing_class,
            relevant_imports=relevant_imports,
            surrounding_code=surrounding_code,
        )
