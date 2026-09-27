"""
JOCKY Diagnostics Subsystem
Provides error reporting, codes, and pretty-printing diagnostics for the compiler.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class DiagnosticSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DiagnosticCode(str, Enum):
    # Lexical Errors (1000 - 1099)
    UNEXPECTED_CHARACTER = "JOCKY-E1000"
    UNTERMINATED_STRING = "JOCKY-E1001"
    INVALID_NUMBER = "JOCKY-E1002"

    # Syntax Errors (1100 - 1199)
    SYNTAX_ERROR = "JOCKY-E1100"
    EXPECTED_SEMICOLON = "JOCKY-E1101"
    EXPECTED_LBRACE = "JOCKY-E1102"
    EXPECTED_RBRACE = "JOCKY-E1103"
    EXPECTED_LPAREN = "JOCKY-E1104"
    EXPECTED_RPAREN = "JOCKY-E1105"
    EXPECTED_IDENTIFIER = "JOCKY-E1106"
    EXPECTED_STRING = "JOCKY-E1107"
    MALFORMED_CALL = "JOCKY-E1108"
    EXPECTED_ANALYSIS = "JOCKY-E1109"

    # Semantic Errors (2000 - 2099)
    UNKNOWN_NAMESPACE = "JOCKY-E2001"
    UNKNOWN_FUNCTION = "JOCKY-E2002"
    WRONG_ARGUMENT_COUNT = "JOCKY-E2003"
    ARGUMENT_COUNT_MISMATCH = "JOCKY-E2003"
    MISSING_ARGUMENT = "JOCKY-E2004"
    WRONG_ARGUMENT_TYPE = "JOCKY-E2005"
    ARGUMENT_TYPE_MISMATCH = "JOCKY-E2005"
    DUPLICATE_ANALYSIS_NAME = "JOCKY-E2006"
    UNKNOWN_IDENTIFIER = "JOCKY-E2007"


@dataclass
class Diagnostic:
    code: DiagnosticCode
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    line: int = 1
    column: int = 1
    offset: int = 0
    length: int = 1
    file: str = "<input>"
    help_text: Optional[str] = None
    source_line: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "code": self.code.value if isinstance(self.code, DiagnosticCode) else str(self.code),
            "severity": self.severity.value if isinstance(self.severity, DiagnosticSeverity) else str(self.severity),
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "offset": self.offset,
        }
        if self.help_text:
            d["help"] = self.help_text
        return d

    def format_rust_style(self, source_code: Optional[str] = None) -> str:
        """Formats the diagnostic in a rich, Rust/Clang-like style."""
        code_str = self.code.value if isinstance(self.code, DiagnosticCode) else str(self.code)
        header = f"{code_str}: {self.message.splitlines()[0]}"
        location = f"  --> {self.file}:{self.line}:{self.column}"

        line_snippet = ""
        if source_code:
            lines = source_code.splitlines()
            if 0 < self.line <= len(lines):
                raw_line = lines[self.line - 1]
                gutter_num = f"{self.line:>4} | "
                gutter_blank = f"{' ':>4} | "
                pointer = " " * max(0, self.column - 1) + "^" * max(1, self.length)
                line_snippet = f"\n{gutter_num}{raw_line}\n{gutter_blank}{pointer}"
        elif self.source_line:
            gutter_num = f"{self.line:>4} | "
            gutter_blank = f"{' ':>4} | "
            pointer = " " * max(0, self.column - 1) + "^" * max(1, self.length)
            line_snippet = f"\n{gutter_num}{self.source_line}\n{gutter_blank}{pointer}"

        help_part = ""
        if self.help_text:
            gutter_blank = "      "
            help_lines = self.help_text.splitlines()
            help_part = f"\n{gutter_blank}help: {help_lines[0]}"
            for h in help_lines[1:]:
                help_part += f"\n{gutter_blank}      {h}"

        # If there are additional detail lines in the message itself
        msg_lines = self.message.splitlines()
        extra_msg = ""
        if len(msg_lines) > 1:
            extra_msg = "\n" + "\n".join(msg_lines[1:])

        return f"{header}\n{location}{line_snippet}{help_part}{extra_msg}"


class DiagnosticReporter:
    def __init__(self, source_code: str = "", filename: str = "<input>"):
        self.source_code = source_code
        self.filename = filename
        self.diagnostics: List[Diagnostic] = []

    def add(self, diagnostic: Diagnostic):
        if not diagnostic.file or diagnostic.file == "<input>":
            diagnostic.file = self.filename
        self.diagnostics.append(diagnostic)

    def error(
        self,
        code: DiagnosticCode,
        message: str,
        line: int = 1,
        column: int = 1,
        offset: int = 0,
        length: int = 1,
        help_text: Optional[str] = None,
    ):
        self.add(
            Diagnostic(
                code=code,
                message=message,
                severity=DiagnosticSeverity.ERROR,
                line=line,
                column=column,
                offset=offset,
                length=length,
                file=self.filename,
                help_text=help_text,
            )
        )

    def has_errors(self) -> bool:
        return any(d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics)

    def format_all(self) -> str:
        return "\n\n".join(d.format_rust_style(self.source_code) for d in self.diagnostics)
