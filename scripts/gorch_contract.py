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

2026-11-09 — strictness had four holes, each proved by feeding one malformed row:

1. An **indented** card row (`  | T1 s1-...`) was never seen: the block builder only
   collected lines starting with `|`, so the indent dropped the row before any regex
   ran. Indent is not cell content; the builder now strips it.
2. `T2s1-...` — the task id and the card id with no separating space — did not match
   the `^T\\d+\\s+...` head, so it fell through as "a task row that names no card".
   A task id followed immediately by something that opens like a card id is now refused.
3. `ACC-1x` matched a prefix-only `^\\|\\s*ACC-\\d+`, so it was accepted as a gate and
   compared against `ACC-1`. Gate ids are now matched whole (`ACC-<digits>`, anchored).
4. `ACC-X` matched nothing at all, so it disappeared. Any first cell that opens like
   `ACC-`/`ACC_` but is not a whole `ACC-<digits>` id is refused instead.
"""

from __future__ import annotations

import re

# A card reference sits in the second cell of a task row: `| T1 s1-host-shell-envcheck | ...`.
_CARD_ID = re.compile(r"^(?:s1-[a-z0-9][a-z0-9-]*|orb-w\d+-[a-z0-9][a-z0-9-]*)$")
# Anything that starts like one of those ids is a card reference that failed to parse,
# rather than a task row that never meant to name a card.
_CARD_LOOKS = re.compile(r"^(?:s1|orb-w)", re.IGNORECASE)
# A task row's first cell is the task id, optionally followed by a card reference.
# `(?![0-9])` keeps `T1` from matching inside `T10`; group 1 is everything after the id.
_TASK_CELL = re.compile(r"^T\d+(?![0-9])(.*)$")
# Acceptance gate ids are matched whole, and only a table cell can open a row.
_ACC_ID = re.compile(r"^ACC-\d+$")
_ACC_LOOKS = re.compile(r"^ACC[-_]", re.IGNORECASE)


def _blocks(text: str) -> list[list[str]]:
    """Group consecutive table lines, so a repeat can be judged inside one table only.

    The leading indent of a nested table is not part of any cell, so it is ignored
    when deciding whether a line is a table row. It used to hide a card row entirely.
    """
    blocks, current = [], []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


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
            cells = _cells(line)
            if not cells or not cells[0]:
                raise ValueError(f"a table row has no first cell: {line.strip()[:80]}")
            head = _TASK_CELL.match(cells[0])
            if not head:
                continue                      # not a task row
            tail = head.group(1)
            if not tail:
                continue                      # `| T1 | 文件 | 门 |` names no card
            if not tail[0].isspace():
                # `T2s1-...`: the id ran into the card reference with no separator.
                if _CARD_LOOKS.match(tail.strip()):
                    raise ValueError(
                        "a task id and a card reference are not separated by whitespace: "
                        f"{cells[0][:40]}")
                continue                      # some other non-row shape
            candidate = tail.strip()
            if not candidate or not _CARD_LOOKS.match(candidate):
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
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue                          # prose mentioning a gate is not a gate
        cells = _cells(line)
        if not cells or not cells[0]:
            continue
        gate_id = cells[0]
        if not _ACC_LOOKS.match(gate_id):
            continue
        if not _ACC_ID.match(gate_id):
            raise ValueError(
                f"line {number}: acceptance row {gate_id[:24]!r} opens like a gate but is "
                "not a whole ACC-<digits> id; a gate that cannot be named cannot be judged")
        if len(cells) < 3:
            raise ValueError(f"line {number}: an acceptance row has fewer than three cells")
        criterion, how = cells[1], cells[2]
        if not criterion or not how:
            raise ValueError(f"line {number}: gate {gate_id} has an empty criterion or method")
        seen[gate_id] = seen.get(gate_id, 0) + 1
        found.append({"id": gate_id, "criterion": criterion, "how": how})
    duplicates = [gid for gid, count in seen.items() if count > 1]
    if duplicates:
        raise ValueError(
            f"card reuses gate ids: {duplicates}; one verdict would cover several criteria")
    return found
