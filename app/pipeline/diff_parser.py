from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from unidiff import PatchSet


@dataclass(frozen=True)
class DiffChange:
    file_path: str
    line_number: Optional[int]
    content: str
    change_type: str


def parse_diff(diff_text: str) -> List[DiffChange]:
    patch = PatchSet(diff_text)
    changes: List[DiffChange] = []

    for file in patch:
        for hunk in file:
            for line in hunk:
                if not (line.is_added or line.is_removed):
                    continue
                line_number = line.target_line_no if line.is_added else line.source_line_no
                changes.append(
                    DiffChange(
                        file_path=file.path,
                        line_number=line_number,
                        content=line.value.rstrip("\n"),
                        change_type="added" if line.is_added else "removed",
                    )
                )

    return changes
