import re

from app.schemas.code_context import DiffFile, DiffHunk, DiffLine, FileStatus

HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


class DiffParser:
    """
    Parses Git Unified Diffs into structured DiffFile and DiffHunk objects,
    calculating exact 1-based line coordinates for GitHub inline commenting.
    """

    @classmethod
    def parse_diff(cls, diff_text: str) -> list[DiffFile]:
        """Parse raw unified diff text into a list of DiffFile objects."""
        if not diff_text or not diff_text.strip():
            return []

        files: list[DiffFile] = []
        raw_file_sections = re.split(r"(?=^diff --git )", diff_text, flags=re.MULTILINE)

        for section in raw_file_sections:
            section = section.strip()
            if not section or not section.startswith("diff --git"):
                continue

            diff_file = cls._parse_file_section(section)
            if diff_file:
                files.append(diff_file)

        return files

    @classmethod
    def _parse_file_section(cls, section: str) -> DiffFile | None:
        lines = section.splitlines()
        first_line = lines[0]

        # Extract file paths from 'diff --git a/path b/path'
        git_header_match = re.match(r"^diff --git a/(.*) b/(.*)$", first_line)
        if not git_header_match:
            return None

        old_path = git_header_match.group(1)
        new_path = git_header_match.group(2)

        status: FileStatus = "modified"
        is_binary = False

        # Scan header lines for metadata
        hunk_start_index = -1
        for idx, line in enumerate(lines[1:], start=1):
            if line.startswith("new file mode"):
                status = "added"
            elif line.startswith("deleted file mode"):
                status = "deleted"
            elif line.startswith("rename from"):
                status = "renamed"
                old_path = line.split("rename from ", 1)[1].strip()
            elif line.startswith("rename to"):
                status = "renamed"
                new_path = line.split("rename to ", 1)[1].strip()
            elif "Binary files" in line and "differ" in line:
                is_binary = True
            elif line.startswith("@@"):
                hunk_start_index = idx
                break

        if is_binary:
            return DiffFile(
                old_path=old_path,
                new_path=new_path,
                status=status,
                is_binary=True,
                hunks=[],
            )

        if hunk_start_index == -1:
            # File metadata change only (e.g. chmod or empty file)
            return DiffFile(
                old_path=old_path,
                new_path=new_path,
                status=status,
                hunks=[],
            )

        hunks = cls._parse_hunks(lines[hunk_start_index:])

        additions = sum(1 for hunk in hunks for line in hunk.lines if line.type == "add")
        deletions = sum(1 for hunk in hunks for line in hunk.lines if line.type == "delete")

        return DiffFile(
            old_path=old_path,
            new_path=new_path,
            status=status,
            hunks=hunks,
            is_binary=False,
            additions_count=additions,
            deletions_count=deletions,
        )

    @classmethod
    def _parse_hunks(cls, lines: list[str]) -> list[DiffHunk]:
        hunks: list[DiffHunk] = []
        current_hunk: DiffHunk | None = None
        current_old_line = 0
        current_new_line = 0

        for line in lines:
            if line.startswith("@@"):
                # Save previous hunk
                if current_hunk:
                    hunks.append(current_hunk)

                match = HUNK_HEADER_REGEX.match(line)
                if not match:
                    continue

                old_start = int(match.group(1))
                old_lines = int(match.group(2)) if match.group(2) is not None else 1
                new_start = int(match.group(3))
                new_lines = int(match.group(4)) if match.group(4) is not None else 1
                header_context = match.group(5).strip()

                current_old_line = old_start
                current_new_line = new_start

                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_lines=old_lines,
                    new_start=new_start,
                    new_lines=new_lines,
                    header=header_context,
                    lines=[],
                    valid_new_lines=[],
                )
                continue

            if current_hunk is None:
                continue

            if line.startswith("+"):
                diff_line = DiffLine(
                    type="add",
                    content=line[1:],
                    old_line_number=None,
                    new_line_number=current_new_line,
                    is_commentable=True,
                )
                current_hunk.lines.append(diff_line)
                current_hunk.valid_new_lines.append(current_new_line)
                current_new_line += 1

            elif line.startswith("-"):
                diff_line = DiffLine(
                    type="delete",
                    content=line[1:],
                    old_line_number=current_old_line,
                    new_line_number=None,
                    is_commentable=False,
                )
                current_hunk.lines.append(diff_line)
                current_old_line += 1

            elif line.startswith(" ") or line == "":
                # Context line
                content = line[1:] if line.startswith(" ") else line
                diff_line = DiffLine(
                    type="context",
                    content=content,
                    old_line_number=current_old_line,
                    new_line_number=current_new_line,
                    is_commentable=True,
                )
                current_hunk.lines.append(diff_line)
                current_hunk.valid_new_lines.append(current_new_line)
                current_old_line += 1
                current_new_line += 1

            elif line.startswith("\\ No newline at end of file"):
                continue

        if current_hunk:
            hunks.append(current_hunk)

        return hunks

    @classmethod
    def get_commentable_lines_for_file(cls, diff_file: DiffFile) -> set[int]:
        """Returns set of all valid line numbers in the new file that GitHub will accept for inline comments."""
        valid_lines: set[int] = set()
        for hunk in diff_file.hunks:
            valid_lines.update(hunk.valid_new_lines)
        return valid_lines
