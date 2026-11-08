from app.github.diff_parser import DiffParser

SAMPLE_MODIFIED_DIFF = """diff --git a/app/core/security.py b/app/core/security.py
index 1111111..2222222 100644
--- a/app/core/security.py
+++ b/app/core/security.py
@@ -10,6 +10,8 @@ def verify_token(token: str) -> bool:
     if not token:
         return False
+    if token.startswith("test_"):
+        return True
     return False
"""

SAMPLE_MULTI_HUNK_DIFF = """diff --git a/app/service.py b/app/service.py
index aaaaaaa..bbbbbbb 100644
--- a/app/service.py
+++ b/app/service.py
@@ -5,4 +5,5 @@ class Service:
     def __init__(self):
+        self.enabled = True
         pass
@@ -20,6 +21,7 @@ class Service:
     def process(self):
-        return None
+        val = 42
+        return val
"""

SAMPLE_NEW_FILE_DIFF = """diff --git a/app/new_module.py b/app/new_module.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/app/new_module.py
@@ -0,0 +1,4 @@
+def greet(name: str) -> str:
+    return f"Hello, {name}!"
"""

SAMPLE_DELETED_FILE_DIFF = """diff --git a/app/legacy.py b/app/legacy.py
deleted file mode 100644
index 4444444..0000000
--- a/app/legacy.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def deprecated():
-    pass
"""

SAMPLE_RENAMED_DIFF = """diff --git a/app/old_name.py b/app/new_name.py
similarity index 98%
rename from app/old_name.py
rename to app/new_name.py
index 5555555..6666666 100644
--- a/app/old_name.py
+++ b/app/new_name.py
@@ -1,3 +1,3 @@
-version = "1.0"
+version = "2.0"
"""

SAMPLE_BINARY_DIFF = """diff --git a/assets/logo.png b/assets/logo.png
index 7777777..8888888 100644
Binary files a/assets/logo.png and b/assets/logo.png differ
"""


def test_parse_empty_diff():
    assert DiffParser.parse_diff("") == []
    assert DiffParser.parse_diff("   \n  ") == []


def test_parse_single_modified_file():
    files = DiffParser.parse_diff(SAMPLE_MODIFIED_DIFF)
    assert len(files) == 1
    f = files[0]
    assert f.old_path == "app/core/security.py"
    assert f.new_path == "app/core/security.py"
    assert f.status == "modified"
    assert f.is_binary is False
    assert f.additions_count == 2
    assert f.deletions_count == 0
    assert len(f.hunks) == 1

    hunk = f.hunks[0]
    assert hunk.old_start == 10
    assert hunk.new_start == 10
    assert hunk.new_lines == 8
    assert "def verify_token" in hunk.header

    # Verify line coordinates
    commentable_lines = DiffParser.get_commentable_lines_for_file(f)
    assert 12 in commentable_lines  # first added line
    assert 13 in commentable_lines  # second added line
    assert 10 in commentable_lines  # context line
    assert 14 in commentable_lines  # end context line


def test_parse_multi_hunk_file():
    files = DiffParser.parse_diff(SAMPLE_MULTI_HUNK_DIFF)
    assert len(files) == 1
    f = files[0]
    assert len(f.hunks) == 2
    assert f.additions_count == 3
    assert f.deletions_count == 1

    # Hunk 1
    h1 = f.hunks[0]
    assert h1.old_start == 5
    assert h1.new_start == 5
    assert 6 in h1.valid_new_lines

    # Hunk 2
    h2 = f.hunks[1]
    assert h2.old_start == 20
    assert h2.new_start == 21
    assert 22 in h2.valid_new_lines
    assert 23 in h2.valid_new_lines


def test_parse_new_file():
    files = DiffParser.parse_diff(SAMPLE_NEW_FILE_DIFF)
    assert len(files) == 1
    f = files[0]
    assert f.status == "added"
    assert f.new_path == "app/new_module.py"
    assert f.additions_count == 2
    assert len(f.hunks) == 1
    assert 1 in f.hunks[0].valid_new_lines
    assert 2 in f.hunks[0].valid_new_lines


def test_parse_deleted_file():
    files = DiffParser.parse_diff(SAMPLE_DELETED_FILE_DIFF)
    assert len(files) == 1
    f = files[0]
    assert f.status == "deleted"
    assert f.old_path == "app/legacy.py"
    assert f.deletions_count == 2
    assert f.additions_count == 0


def test_parse_renamed_file():
    files = DiffParser.parse_diff(SAMPLE_RENAMED_DIFF)
    assert len(files) == 1
    f = files[0]
    assert f.status == "renamed"
    assert f.old_path == "app/old_name.py"
    assert f.new_path == "app/new_name.py"
    assert f.additions_count == 1
    assert f.deletions_count == 1


def test_parse_binary_file():
    files = DiffParser.parse_diff(SAMPLE_BINARY_DIFF)
    assert len(files) == 1
    f = files[0]
    assert f.is_binary is True
    assert len(f.hunks) == 0


def test_parse_composite_diff():
    composite = f"{SAMPLE_MODIFIED_DIFF}\n{SAMPLE_NEW_FILE_DIFF}\n{SAMPLE_BINARY_DIFF}"
    files = DiffParser.parse_diff(composite)
    assert len(files) == 3
    assert files[0].new_path == "app/core/security.py"
    assert files[1].new_path == "app/new_module.py"
    assert files[2].new_path == "assets/logo.png"
