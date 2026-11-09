"""The one parser for the two tables every G-ORCH script reads.

`dispatch-work-order.py` and `freeze-work-order.py` each enumerated order cards with
their own regex, and `audit-work-order.py` and `freeze-work-order.py` each parsed the
card's acceptance table with their own loop. Three copies of one rule are three
chances for one of them to skip a row: a row that "looks like" a card reference but
did not match was dropped, and an order that named the same card twice was
de-duplicated instead of refused.

Both parsers are strict on purpose. A row that cannot be read is a failure, not a row
to ignore — the gate has to be able to say it saw every row the document declares,
because a silently skipped row and an absent row look identical in a receipt.

The one deliberate exception is a repeated card id *across* tables. `wo-s1-host-shell`
names each of its five cards once in the task table and once in the write-scope table;
that is the same card listed twice for two purposes, not two tasks competing for one
artifact. A repeat *inside* one table is still refused.
"""

from __future__ import annotations

import re

# A card reference sits in the second cell of a task row: `| T1 s1-host-shell-envcheck | ...`.
_CARD_ID = re.compile(r"^(?:s1-[a-z0-9][a-z0-9-]*|orb-w\d+-[a-z0-9][a-z0-9-]*)$")
# Anything that starts like one of those ids is a card reference that failed to parse,
# rather than a task row that never meant to name a card.
_CARD_LOOKS = re.compile(r"^(?:s1|orb-w)", re.IGNORECASE)
_TASK_ROW = re.compile(r"^\|\s*T\d+")


def _blocks(text: str) -> list[list[str]]:
    """Group consecutive table lines, so a repeat can be judged inside one table only."""
    blocks, current = [], []
    for line in text.splitlines():
        if line.startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def order_cards(text: str) -> list[str]:
    """Card ids the order references, in first-seen order, across all its tables.

    Raises ValueError when a task row opens like a card reference but does not
    parse, or when one table names the same card twice. Both are refusals rather
    than drops: the receipt has to be able to name the whole set.
    """
    found: list[str] = []
    seen_anywhere: set[str] = set()
    for block in _blocks(text):
        in_block: set[str] = set()
        for line in block:
            if not _TASK_ROW.match(line):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells:
                raise ValueError(f"a task row has no cells: {line.strip()[:80]}")
            # The card id shares the first cell with the task number:
            # `| T1 s1-host-shell-envcheck | 标题 | ...`
            head = re.match(r"^T\d+\s+(.+)$", cells[0])
            if not head:
                continue                      # a task row that names no card
            candidate = head.group(1).strip()
            if not _CARD_LOOKS.match(candidate):
                continue                      # a task row that names no card
            if not _CARD_ID.match(candidate):
                raise ValueError(
                    f"a task row looks like a card reference but is not one: {candidate[:40]}")
            if candidate in in_block:
                raise ValueError(
                    f"one table names card {candidate} more than once; two rows for one "
                    "card leave it unclear which row the receipt is bound to")
            in_block.add(candidate)
            if candidate not in seen_anywhere:
                seen_anywhere.add(candidate)
                found.append(candidate)
    return found


_ACC_HEAD = re.compile(r"^\|\s*ACC-\d+")


def acc_rows(text: str) -> list[dict]:
    """Acceptance gates as {id, criterion, how} from the card's table.

    Every row that opens with an ACC id has to carry three non-empty cells. A row
    that is recognised as a gate but has no criterion, or no way to judge it, used to
    be skipped — which let a card declare a gate nothing would ever check. Duplicate
    ids are refused for the same reason: one verdict would stand in for two criteria.
    """
    found: list[dict] = []
    seen: dict[str, int] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not _ACC_HEAD.match(line.strip()):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            raise ValueError(f"line {number}: an acceptance row has fewer than three cells")
        gate_id, criterion, how = cells[0], cells[1], cells[2]
        if not criterion or not how:
            raise ValueError(f"line {number}: gate {gate_id} has an empty criterion or method")
        seen[gate_id] = seen.get(gate_id, 0) + 1
        found.append({"id": gate_id, "criterion": criterion, "how": how})
    duplicates = [gid for gid, count in seen.items() if count > 1]
    if duplicates:
        raise ValueError(
            f"card reuses gate ids: {duplicates}; one verdict would cover several criteria")
    return found
