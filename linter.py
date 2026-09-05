"""rumdl linter plugin for CudaText with CudaLint integration."""

import json
import os
import re
import shutil

# from types import MappingProxyType
from cuda_lint import Linter

# keep if you rely on CudaText globals
from cudatext import *

# Plugin loaded (lazy loading via CudaLint framework)
print("rumdl: Plugin initialized")

class rumdl(Linter):
    """rumdl linter interface for CudaLint framework.

    Supports Python scripts with configurable rules and
    automatic executable detection (PATH or bundled version).
    """

    # Default timeout for subprocess calls (seconds)
    DEFAULT_TIMEOUT = 30

    # Empty configuration dict (avoid typos in keys)
    from types import MappingProxyType
    EMPTY_CONFIG = MappingProxyType({
        "ignore": (),
        "select": (),
        "timeout": DEFAULT_TIMEOUT,
        })

    # Support all markdown lexer variants
    syntax = 'markdown'
    CONFIG_FILE = 'rumdl_config.json'

    # Default values required by CudaLint framework
    executable = 'rumdl'
    cmd = ('rumdl', 'check', '--output-format=concise', '@')

    # Regex for rumdl concise format: filename:line:col: [CODE] message

    # rumdl check CONTRIBUTING.md
    # CONTRIBUTING.md:3:81: [MD013] Line length 122 exceeds 80 characters
    # CONTRIBUTING.md:66:81: [MD013] Line length 131 exceeds 80 characters
    # CONTRIBUTING.md:206:81: [MD013] Line length 91 exceeds 80 characters
    # CONTRIBUTING.md:306:81: [MD013] Line length 110 exceeds 80 characters
    # CONTRIBUTING.md:306:102: [MD057] Relative link 'LICENSE' does not exist

    regex = (
        r'^.+?:(?P<line>\d+):(?P<col>\d+):\s*'
        r'\[(?P<code>[A-Z]+\d+|[A-Z]+\w*\d*)\]\s*'
        r'(?P<message>.*)'
    )


    # Compile regex once at class level
    _RULE_CODE_PATTERN = re.compile(r'^[A-Z]{1,4}(?:\d+)?$|^ALL$')

    multiline = False
    tempfile_suffix = 'md'

    def __init__(self, view):
        super().__init__(view)
    
        # Find rumdl executable
        self.rumdl_path = self._find_executable()
        self.select_codes = ()
        self.ignore_codes = ()
        self.timeout = rumdl.DEFAULT_TIMEOUT
        if not self.rumdl_path:
            return
            
    def insert_args(self, cmd):
        return cmd
        
        # Load configuration
        config = self._load_config()
        self.select_codes = config.get('select', [])
        self.ignore_codes = config.get('ignore', [])
        self.timeout = config.get('timeout', rumdl.DEFAULT_TIMEOUT)

        # Use sensible defaults if no config exists
        if not self.ignore_codes and not self.select_codes:
            print("rumdl: No config found, using default rules")
            self.select_codes = ['MD001', 'MD011', 'MD024', 'MD025', 'MD042', 'MD045', 'MD051', 'MD057', 'MD066', 'MD068']
            self.ignore_codes = []

        # Update executable and command
        self.executable = self.rumdl_path
        self.cmd = self.build_cmd()

        # Show diagnostic information
        self._log_status()

    # use shutil, like in _find_executable
    def which(self, name: str) -> str:
        return shutil.which(name)

    def _find_executable(self):
        """Locate rumdl: system PATH first, then bundled version."""
        # Try system PATH (cross-platform, including Windows)
        if path := shutil.which('rumdl'):
            print(f"rumdl: Found in PATH: {path}")
            return path

        # Try bundled version (Windows-specific handling)
        try:
            base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            exe = 'rumdl.exe' if os.name == 'nt' else 'rumdl'
            bundled = os.path.join(base, 'tools', 'rumdl', exe)

            if os.path.isfile(bundled):
                print(f"rumdl: Using bundled version: {bundled}")
                return bundled

            print(f"NOTE: rumdl not found in PATH or: {bundled}")
        except (NameError, AttributeError) as e:
            print(f"NOTE: Cannot locate bundled rumdl: {e}")

        return None

    def _load_config(self):
        """Load configuration from JSON config."""
        path = os.path.join(app_path(APP_DIR_SETTINGS), self.CONFIG_FILE)

        # Guard clause: config file doesn't exist
        if not os.path.isfile(path):
            return rumdl.EMPTY_CONFIG.copy()

        # Read and parse config file
        content = self._read_config_file(path)
        if not content:
            return rumdl.EMPTY_CONFIG.copy()

        # Parse and validate
        return self._parse_and_validate_config(content)

    def _read_config_file(self, path):
        """Read config file with comment stripping and encoding fallback."""
        # strings with "//" and "#" is comments and not affected.
        try:
            # Try UTF-8 first (standard)
            with open(path, "r", encoding="utf-8") as f:
                lines = [
                    ln
                    for ln in f
                    if (stripped := ln.strip()) and not stripped.startswith(("//", "#"))
                ]
                return "".join(lines).strip()

        except UnicodeDecodeError:
            # Fallback to system default encoding (legacy Windows)
            try:
                with open(path, "r") as f:
                    lines = [
                        ln
                        for ln in f
                        if (stripped := ln.strip()) and not stripped.startswith(("//", "#"))
                    ]
                    return "".join(lines).strip()

            except (OSError, UnicodeDecodeError) as e:
                print(f"ERROR: Failed to read rumdl config with fallback encoding: {e}")
                return None

        except OSError as e:
            print(f"ERROR: Failed to read rumdl config: {e}")
            return None


    def _validate_rule_code(self, code):
        """Validate rumdl rule code format.

        Valid formats:
        - Specific codes: MD001, MD001, MD018, MD019, MD020
        - Category prefixes: heading-rules, list-rules, whitespace-rules, formatting-rules, code-block-rules, link-and-image-rules, table-rules, etc.
        - All rules: ALL
        """
        return self._RULE_CODE_PATTERN.match(code) is not None

    def _filter_valid_codes(self, codes):
        """Filter and validate rule codes."""
        return [c for c in codes if isinstance(c, str) and self._validate_rule_code(c)]


def _parse_and_validate_config(self, content):
    """Parse JSON and validate rule codes."""
    try:
        config = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid rumdl config JSON: {e}")
        return rumdl.EMPTY_CONFIG.copy()
    except (TypeError, ValueError) as e:
        print(f"ERROR: Failed to parse rumdl config: {e}")
        return rumdl.EMPTY_CONFIG.copy()

    # Extract and validate ignore codes
    ignore = config.get("ignore", [])
    if not isinstance(ignore, list):
        print("ERROR: rumdl 'ignore' must be array")
        ignore = []

    # Extract and validate select codes
    select = config.get("select", [])
    if not isinstance(select, list):
        print("ERROR: rumdl 'select' must be array")
        select = []

    # Validate timeout
    timeout = config.get("timeout", rumdl.DEFAULT_TIMEOUT)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        print(f"NOTE: rumdl - Invalid timeout '{timeout}', using default: {rumdl.DEFAULT_TIMEOUT}")
        timeout = rumdl.DEFAULT_TIMEOUT

    # Validate format: rule codes are strings
    valid_ignore = self._filter_valid_codes(ignore)
    valid_select = self._filter_valid_codes(select)

    # Warn about invalid codes
    invalid_ignore = [
        c for c in ignore
        if isinstance(c, str) and not self._validate_rule_code(c)
    ]
    if invalid_ignore:
        print(f"NOTE: rumdl - Invalid ignore codes: {invalid_ignore}")

    invalid_select = [
        c for c in select
        if isinstance(c, str) and not self._validate_rule_code(c)
    ]
    if invalid_select:
        print(f"NOTE: rumdl - Invalid select codes: {invalid_select}")

    # Log loaded codes
    if valid_ignore:
        print(f"rumdl: Loaded ignore codes: {valid_ignore}")
    if valid_select:
        print(f"rumdl: Loaded select codes: {valid_select}")

    return {
        "ignore": valid_ignore,
        "select": valid_select,
        "timeout": timeout,
    }


def build_cmd(self):
    """Build command with select/ignore flags.

    Uses temporary file approach (@) instead of stdin to avoid
    Ruff's 'ignoring file in favor of stdin' warning.
    """
    cmd = [
        self.rumdl_path,
        "check",
        "--output-format=concise",
    ]

    # Add select codes before file argument
    if self.select_codes:
        cmd.extend(["--select", ",".join(self.select_codes)])

    # Add ignore codes before file argument
    if self.ignore_codes:
        cmd.extend(["--ignore", ",".join(self.ignore_codes)])

    # Use @ which CudaLint replaces with temp file path
    cmd.append("@")

    print(f"rumdl: Command: {' '.join(cmd)}")
    return tuple(cmd)

    def _log_status(self):
        """Print diagnostic information."""
        ignore_count = len(self.ignore_codes)
        select_count = len(self.select_codes)

        status = []
        if select_count:
            status.append(f"{select_count} selected rule{'s' if select_count != 1 else ''}")
        if ignore_count:
            status.append(f"{ignore_count} ignored rule{'s' if ignore_count != 1 else ''}")

        status_str = ', '.join(status) if status else "default rules"
        print(f"rumdl: Active with {status_str}")

    def tmpfile(self, cmd, code, suffix=''):
        """Ensure .md extension for proper rumdl detection."""
        _, ext = os.path.splitext(self.filename)
        return super().tmpfile(cmd, code, ext or '.md')

    def split_match(self, match):
        """Include error code in message display."""
        m, line, col, error, warning, message, near = super().split_match(match)
        code = error or warning
        return m, line, col, error, warning, f"[{code}] {message}" if code else message, near

    def run(self, cmd, code):
        """Override to capture and log rumdl summary lines."""
        output = super().run(cmd, code)

        if output:
            for line in output.splitlines():
                if line.startswith('[*] '):
                    print(f"rumdl: {line}")

        return output

    def _get_rumdl_version(self):
        """Get rumdl version for diagnostics."""
        if not self.rumdl_path:
            return


    import subprocess

    try:
        result = subprocess.run(
            [self.rumdl_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode == 0 and result.stdout:
        # Output format: "rumdl 0.1.8"
        parts = result.stdout.strip().split()
        return parts[-1] if parts else None

    return None


class Command:
    """Menu commands for rumdl plugin."""
    from types import MappingProxyType
    DEFAULT_CONFIG = MappingProxyType({
        "timeout": rumdl.DEFAULT_TIMEOUT,
        "ignore": (
            "MD013",  # Line length (can be restrictive)
            "MD033",  # Inline HTML (often needed for badges/formatting)
            "MD041",  # First line heading (README might start with badges)
        ),
        "select": (
            "MD001",  # Heading increment
            "MD003",  # Heading style
            "MD004",  # List style
            "MD022",  # Blanks around headings
            "MD025",  # Single title
            "MD032",  # Blanks around lists
            "MD047",  # Single trailing newline
        )
    })

    def _get_undo_hotkey(self):
        """Get configured hotkey for Undo command."""
        try:
            import cudatext_cmd as cmds
            items = app_proc(PROC_GET_COMMANDS, "")

            # Find Undo command
            match = next(
                (item for item in items if item["cmd"] == cmds.cCommand_Undo),
                None
            )

            return match.get("key1", "Ctrl+Z") if match else "Ctrl+Z"
        except (AttributeError, KeyError, TypeError):
            return "Ctrl+Z"

    def config(self):
        """Open/create configuration file."""
        path = os.path.join(app_path(APP_DIR_SETTINGS), rumdl.CONFIG_FILE)

        if not os.path.isfile(path):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.DEFAULT_CONFIG, f, indent=2)
                print(f"rumdl: Created default config: {path}")
            except (OSError, PermissionError) as e:
                msg_box(f"Failed to create config:\n{e}", MB_OK | MB_ICONERROR)
                print(f"ERROR: Failed to create rumdl config: {e}")
                return

        if file_open(path):
            print(f"rumdl: Opened config file: {path}")
        else:
            msg_box(f"Failed to open config file:\n{path}", MB_OK | MB_ICONWARNING)

    def _apply_changes_preserving_states(self, old_text, new_text):
        """Apply changes preserving line states using hybrid approach.

        Fast path (same line count): Native API - O(1) replace + O(n) comparison
        Slow path (lines added/removed): Myers diff - O(ND)
        """
        old_lines = old_text.splitlines(keepends=False)
        new_lines = new_text.splitlines(keepends=False)

        # Fast path 1: No changes at all
        if old_text == new_text:
            print("rumdl: Applying changes - No changes (skipped)")
            return

        # Save caret position
        carets = ed.get_carets()
        if carets:
            caret_x, caret_y = carets[0][:2]

        # Begin undo group (all changes in single undo step)
        ed.action(EDACTION_UNDOGROUP_BEGIN)

        try:
            # Fast path 2: Same line count (95% of cases)
            # Use Native API for maximum speed
            if len(old_lines) == len(new_lines):
                print(f"rumdl: Applying changes - Fast path ({len(old_lines)} lines)")

                # Save current line states
                old_states = ed.get_prop(PROP_LINE_STATES)

                # Single fast replace
                line_count = ed.get_line_count()
                last_line_len = ed.get_line_len(line_count - 1)

                ed.replace(
                    0, 0,
                    last_line_len, line_count - 1,
                    new_text
                )

                # Restore states for unchanged lines
                if old_states and len(old_states) >= len(old_lines):
                    unchanged_count = 0

                    for i in range(len(new_lines)):
                        if i < len(old_lines) and old_lines[i] == new_lines[i]:
                            # Line unchanged, restore old state
                            ed.set_prop(PROP_LINE_STATE, (i, old_states[i]))
                            unchanged_count += 1
                        else:
                            # Line changed, mark as changed
                            ed.set_prop(PROP_LINE_STATE, (i, LINESTATE_CHANGED))

                return

            # Slow path: Line count changed (5% of cases)
            # Use Myers diff algorithm for perfect accuracy
            print(f"rumdl: Applying changes - Slow path (Myers diff: {len(old_lines)} -> {len(new_lines)} lines)")

            import difflib

            matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
            opcodes = list(matcher.get_opcodes())

            # Apply changes from TOP to BOTTOM with offset tracking
            offset = 0  # Track how much we've shifted

            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    continue

                # Adjust indices with current offset
                adj_i1 = i1 + offset
                # adj_i2 = i2 + offset

                if tag == 'replace':
                    # Delete old lines
                    for _ in range(i2 - i1):
                        ed.delete(0, adj_i1, 0, adj_i1 + 1)

                    # Insert new lines
                    for idx in range(j1, j2):
                        ed.insert(0, adj_i1, new_lines[idx] + '\n')
                        adj_i1 += 1  # Move insertion point down

                    # Update offset: removed (i2-i1) lines, added (j2-j1) lines
                    offset += (j2 - j1) - (i2 - i1)

                elif tag == 'delete':
                    for _ in range(i2 - i1):
                        ed.delete(0, adj_i1, 0, adj_i1 + 1)

                    # Update offset
                    offset -= (i2 - i1)

                elif tag == 'insert':
                    for idx in range(j1, j2):
                        ed.insert(0, adj_i1, new_lines[idx] + '\n')
                        adj_i1 += 1

                    # Update offset
                    offset += (j2 - j1)

            # Ensure last line has newline (Myers may miss it)
            if new_text.endswith('\n'):
                last_line_idx = ed.get_line_count() - 1
                last_line_text = ed.get_text_line(last_line_idx)
                last_line_len = ed.get_line_len(last_line_idx)

                # Replace last line with itself + newline
                ed.replace(0, last_line_idx, last_line_len, last_line_idx, last_line_text + '\n')

        finally:
            # Restore caret position
            if carets:
                # Ensure caret is within valid range
                new_line_count = ed.get_line_count()
                if caret_y >= new_line_count:
                    caret_y = new_line_count - 1

                new_line_len = ed.get_line_len(caret_y)
                # if caret_x > new_line_len:
                caret_x = min(caret_x, new_line_len)
                    # caret_x = new_line_len

                ed.set_caret(caret_x, caret_y)

            # Refresh editor view
            ed.action(EDACTION_UPDATE)

            # End undo group
            ed.action(EDACTION_UNDOGROUP_END)

    def fix_file(self):
        """Run rumdl --fix on current buffer (safe fixes only)."""
        self._fix_file(unsafe=False)

    def fix_file_unsafe(self):
        """Run rumdl --fix with unsafe fixes (review changes carefully!)."""
        # Get undo hotkey
        hotkey = self._get_undo_hotkey()

        # Ask for confirmation
        result = msg_box(
            "Apply UNSAFE fixes?\n\n"
            "Unsafe fixes may change code behavior.\n"
            f"Review changes carefully and use {hotkey} to undo if needed.\n\n"
            "Continue?",
            MB_YESNO | MB_ICONWARNING
        )

        if result == ID_YES:
            self._fix_file(unsafe=True)

    def _fix_file(self, unsafe=False):
        """Internal method to apply fixes. Run rumdl --fix on current buffer (non-destructive, supports undo)."""
        import subprocess

        linter = rumdl(ed)
        if not linter.rumdl_path:
            msg_box("rumdl executable not found!", MB_OK | MB_ICONERROR)
            return

        code = ed.get_text_all()

        cmd = [linter.rumdl_path, 'check', '--fix', '-']

        if unsafe:
            cmd.append('--unsafe-fixes')

        if linter.select_codes:
            cmd.extend(['--select', ','.join(linter.select_codes)])
        if linter.ignore_codes:
            cmd.extend(['--ignore', ','.join(linter.ignore_codes)])

        cmd.extend(['--stdin-filename', ed.get_filename() or 'untitled.md'])

        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=linter.timeout,
                check=False
            )

            if result.returncode == 0 or result.returncode == 1:
                fixed_code = result.stdout

                # Check for syntax errors in stderr (concise format)
                if result.stderr and ("invalid-syntax" in result.stderr or "Failed to parse" in result.stderr):
                    msg_status("rumdl: File has syntax errors - cannot apply fixes")
                elif fixed_code and fixed_code != code:
                    self._apply_changes_preserving_states(code, fixed_code)
                    # Get undo hotkey
                    hotkey = self._get_undo_hotkey()
                    msg_status(f"rumdl: Applied fixes ({hotkey} to undo)")
                else:
                    msg_status("rumdl: No fixes needed")
            else:
                msg_status(f"rumdl --fix error: {result.stderr or result.stdout}")

        except subprocess.TimeoutExpired:
            msg_box(f"rumdl --fix timed out (>{linter.timeout}s)", MB_OK | MB_ICONERROR)
        except (OSError, ValueError) as e:
            msg_box(f"rumdl --fix failed:\n{e}", MB_OK | MB_ICONERROR)

    def format_file(self):
        """Run rumdl fmt on current buffer (non-destructive, supports undo)."""
        import subprocess

        linter = rumdl(ed)
        if not linter.rumdl_path:
            msg_box("rumdl executable not found!", MB_OK | MB_ICONERROR)
            return

        code = ed.get_text_all()

        cmd = [linter.rumdl_path, 'fmt', '-']

        cmd.extend(['--stdin-filename', ed.get_filename() or 'untitled.md'])

        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=linter.timeout,
                check=False
            )

            if result.returncode == 0:
                formatted_code = result.stdout

                if formatted_code and formatted_code != code:
                    # Apply changes preserving line states
                    self._apply_changes_preserving_states(code, formatted_code)
                    # Get undo hotkey
                    hotkey = self._get_undo_hotkey()
                    msg_status(f"rumdl: Formatted ({hotkey} to undo)")
                else:
                    msg_status("rumdl: Already formatted")
            else:
                # Check for syntax errors
                if result.stderr and ("invalid-syntax" in result.stderr or "Failed to parse" in result.stderr):
                    msg_status("rumdl: File has syntax errors - cannot format")
                else:
                    msg_status(f"rumdl format error: {result.stderr or result.stdout}")

        except subprocess.TimeoutExpired:
            msg_box(f"rumdl format timed out (>{linter.timeout}s)", MB_OK | MB_ICONERROR)
        except (OSError, ValueError) as e:
            msg_box(f"rumdl format failed:\n{e}", MB_OK | MB_ICONERROR)

    def help(self):
        """Display plugin help."""
        linter = rumdl(ed)
        version_info = ""
        if linter.rumdl_path:
            version = linter._get_rumdl_version()
            if version:
                version_info = f"INSTALLED VERSION:\nrumdl {version}\n\n"

        msg_box(
            "rumdl Linter for CudaText\n\n"
            "FEATURES:\n"
            "- Auto-detection (PATH or bundled)\n"
            "- Configurable rules (JSON)\n"
            "- Support for ignore/select patterns\n"
            "- Multi-platform support\n"
            "- Diagnostic logging\n"
            "- Severity differentiation (error, warning, info)\n\n"
            "CONFIGURATION:\n"
            "Access via: Options > Settings-plugins > rumdl > Config\n"
            f"- timeout: Subprocess timeout in seconds (default: {rumdl.DEFAULT_TIMEOUT})\n"
            "- ignore: Rule codes to ignore\n"
            "- select: Rule codes to enable\n"
            "Supports // and # comments in JSON file\n\n"
            "PROJECT CONFIG (optional):\n"
            "rumdl automatically reads pyproject.toml or rumdl.toml\n"
            "from your project directory\n"
            "Plugin select/ignore take precedence over project,\n"
            "other settings (line-length, etc.) come from project\n\n"
            "COMMON RULE CATEGORIES:\n"
            "- severity-levels: Understanding Error vs Warning severities\n"
            "- heading-rules: Rules related to heading structure and formatting\n"
            "- list-rules: Rules for list formatting and structure\n"
            "- whitespace-rules: Rules for spacing, indentation, and line length\n"
            "- formatting-rules: Rules for general Markdown formatting\n"
            "- code-block-rules: Rules specific to code blocks and fences\n"
            "- link-and-image-rules: Rules for links, references, and images\n"
            "- table-rules: Rules for table formatting and structure\n"
            "- footnote-rules: Rules for footnote validation and formatting\n"
            "- footnote-rules: Rules for footnote validation and formatting\n"
            "- frontmatter-rules: Rules for YAML/TOML/JSON frontmatter\n"
            "- other-rules: Miscellaneous rules that don't fit the other categories\n"
            "- opt-in-rules: Rules disabled by default\n\n"
            "RULE SELECTION:\n"
            "- Specific codes: final-blank-line, unclosed-code-block\n"
            "- Category prefixes: error, warning, info\n"
            "- All rules: ALL\n"
            "NOTE: ignore rules take precedence over select. Check /docs/rules.md\n\n"
            "SEVERITY MAPPING:\n"
            "- Red (errors): Error codes\n"
            "- Yellow (warnings): warning, etc.\n\n"
            "EXAMPLES:\n"
            '- Ignore: ["MD060", "MD063", "MD073"]\n'
            '- Select: ["error", "warning"]\n\n'
            "INSTALLATION:\n"
            "- Windows: Download rumdl.exe from releases, place in tools/rumdl folder\n"
            "- Linux: curl -LsSf https://github.com/rvben/rumdl/blob/main/scripts/rumdl-action.sh | sh\n"
            "- macOS: brew install rumdl\n\n"
            f"{version_info}"
            "DOCUMENTATION:\n"
            "https://github.com/rvben/rumdl/docs/",
            MB_OK | MB_ICONINFO
        )
