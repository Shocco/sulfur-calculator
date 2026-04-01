"""Diff tool for comparing old vs new SULFUR calculator JSON data files.

Compares two directories of JSON data and prints a human-readable summary
of additions, removals, and changes for each tracked file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# Files treated as arrays keyed by 'name'
ARRAY_FILES: list[str] = [
    "weapons.json",
    "enchantments.json",
    "scrolls.json",
    "attachments-muzzle.json",
    "attachments-sights.json",
    "attachments-lasers.json",
    "attachments-chamber.json",
    "attachments-chisels.json",
    "attachments-insurance.json",
]

# Special object file with known sub-keys to compare
CALIBER_FILE = "caliber-modifiers.json"


def diff_json_arrays(
    old: list[dict[str, Any]],
    new: list[dict[str, Any]],
    key: str = "name",
) -> tuple[list[str], list[str], list[tuple[str, dict[str, tuple[Any, Any]]]]]:
    """Compare two lists of dicts by a key field.

    Args:
        old: The previous version of the array.
        new: The updated version of the array.
        key: The field name to use as a unique identifier for each item.

    Returns:
        A 3-tuple of:
            added_names: Sorted list of key values present in new but not old.
            removed_names: Sorted list of key values present in old but not new.
            changed_items: List of (name, {field: (old_val, new_val)}) for items
                that exist in both lists but have differing field values.
    """
    old_by_key: dict[str, dict[str, Any]] = {item[key]: item for item in old}
    new_by_key: dict[str, dict[str, Any]] = {item[key]: item for item in new}

    old_keys = set(old_by_key)
    new_keys = set(new_by_key)

    added_names: list[str] = sorted(new_keys - old_keys)
    removed_names: list[str] = sorted(old_keys - new_keys)

    changed_items: list[tuple[str, dict[str, tuple[Any, Any]]]] = []
    for name in sorted(old_keys & new_keys):
        old_item = old_by_key[name]
        new_item = new_by_key[name]
        all_fields = set(old_item) | set(new_item)
        diffs: dict[str, tuple[Any, Any]] = {}
        for field in all_fields:
            old_val = old_item.get(field)
            new_val = new_item.get(field)
            if old_val != new_val:
                diffs[field] = (old_val, new_val)
        if diffs:
            changed_items.append((name, diffs))

    return added_names, removed_names, changed_items


def diff_json_objects(
    old: dict[str, Any],
    new: dict[str, Any],
) -> tuple[list[str], list[str], list[tuple[str, Any, Any]]]:
    """Compare two flat dicts.

    Args:
        old: The previous version of the object.
        new: The updated version of the object.

    Returns:
        A 3-tuple of:
            added_keys: Sorted list of keys present in new but not old.
            removed_keys: Sorted list of keys present in old but not new.
            changed_tuples: List of (key, old_val, new_val) for keys that exist
                in both dicts but have differing values.
    """
    old_keys = set(old)
    new_keys = set(new)

    added_keys: list[str] = sorted(new_keys - old_keys)
    removed_keys: list[str] = sorted(old_keys - new_keys)

    changed_tuples: list[tuple[str, Any, Any]] = [
        (k, old[k], new[k])
        for k in sorted(old_keys & new_keys)
        if old[k] != new[k]
    ]

    return added_keys, removed_keys, changed_tuples


def _print_array_diff(
    filename: str,
    added: list[str],
    removed: list[str],
    changed: list[tuple[str, dict[str, tuple[Any, Any]]]],
) -> None:
    """Print a formatted diff block for an array-keyed file."""
    print(f"\n{'=' * 60}")
    print(f"  {filename}")
    print(f"{'=' * 60}")

    if not added and not removed and not changed:
        print("  (no changes)")
        return

    if added:
        print(f"\n  ADDED ({len(added)}):")
        for name in added:
            print(f"    + {name}")

    if removed:
        print(f"\n  REMOVED ({len(removed)}):")
        for name in removed:
            print(f"    - {name}")

    if changed:
        print(f"\n  CHANGED ({len(changed)}):")
        for name, field_diffs in changed:
            print(f"    ~ {name}")
            for field, (old_val, new_val) in sorted(field_diffs.items()):
                print(f"        {field}: {old_val!r} -> {new_val!r}")


def _print_object_diff(
    label: str,
    added: list[str],
    removed: list[str],
    changed: list[tuple[str, Any, Any]],
    indent: int = 4,
) -> None:
    """Print a formatted diff block for a flat object section."""
    pad = " " * indent

    if not added and not removed and not changed:
        print(f"{pad}(no changes)")
        return

    if added:
        print(f"{pad}ADDED ({len(added)}):")
        for k in added:
            print(f"{pad}  + {k}")

    if removed:
        print(f"{pad}REMOVED ({len(removed)}):")
        for k in removed:
            print(f"{pad}  - {k}")

    if changed:
        print(f"{pad}CHANGED ({len(changed)}):")
        for k, old_val, new_val in changed:
            print(f"{pad}  ~ {k}: {old_val!r} -> {new_val!r}")


def diff_json_files(old_dir: str | Path, new_dir: str | Path) -> None:
    """Compare tracked JSON data files between two directories and print results.

    Compares:
        - weapons.json, enchantments.json, scrolls.json (arrays, key='name')
        - attachments-muzzle.json, attachments-sights.json, attachments-lasers.json,
          attachments-chamber.json, attachments-chisels.json, attachments-insurance.json
          (arrays, key='name')
        - caliber-modifiers.json (object: baseAmmoDamage and calibers sub-objects)

    Args:
        old_dir: Path to the directory containing the old JSON files.
        new_dir: Path to the directory containing the new JSON files.
    """
    old_path = Path(old_dir)
    new_path = Path(new_dir)

    # --- Array files ---
    for filename in ARRAY_FILES:
        old_file = old_path / filename
        new_file = new_path / filename

        if not old_file.exists() and not new_file.exists():
            continue

        if not old_file.exists():
            print(f"\n{'=' * 60}")
            print(f"  {filename}  [NEW FILE]")
            print(f"{'=' * 60}")
            continue

        if not new_file.exists():
            print(f"\n{'=' * 60}")
            print(f"  {filename}  [FILE REMOVED]")
            print(f"{'=' * 60}")
            continue

        old_data: list[dict[str, Any]] = json.loads(old_file.read_text(encoding="utf-8"))
        new_data: list[dict[str, Any]] = json.loads(new_file.read_text(encoding="utf-8"))

        added, removed, changed = diff_json_arrays(old_data, new_data, key="name")
        _print_array_diff(filename, added, removed, changed)

    # --- caliber-modifiers.json ---
    old_cal_file = old_path / CALIBER_FILE
    new_cal_file = new_path / CALIBER_FILE

    print(f"\n{'=' * 60}")
    print(f"  {CALIBER_FILE}")
    print(f"{'=' * 60}")

    if not old_cal_file.exists() and not new_cal_file.exists():
        print("  (file absent in both directories)")
    elif not old_cal_file.exists():
        print("  [NEW FILE]")
    elif not new_cal_file.exists():
        print("  [FILE REMOVED]")
    else:
        old_cal: dict[str, Any] = json.loads(old_cal_file.read_text(encoding="utf-8"))
        new_cal: dict[str, Any] = json.loads(new_cal_file.read_text(encoding="utf-8"))

        # baseAmmoDamage sub-object
        print("\n  [baseAmmoDamage]")
        old_bad: dict[str, Any] = old_cal.get("baseAmmoDamage", {})
        new_bad: dict[str, Any] = new_cal.get("baseAmmoDamage", {})
        added_k, removed_k, changed_t = diff_json_objects(old_bad, new_bad)
        _print_object_diff("baseAmmoDamage", added_k, removed_k, changed_t, indent=4)

        # calibers sub-object (each value is itself a dict; compare as nested)
        print("\n  [calibers]")
        old_cals: dict[str, Any] = old_cal.get("calibers", {})
        new_cals: dict[str, Any] = new_cal.get("calibers", {})

        cal_added = sorted(set(new_cals) - set(old_cals))
        cal_removed = sorted(set(old_cals) - set(new_cals))

        if cal_added:
            print(f"    ADDED ({len(cal_added)}):")
            for c in cal_added:
                print(f"      + {c}")

        if cal_removed:
            print(f"    REMOVED ({len(cal_removed)}):")
            for c in cal_removed:
                print(f"      - {c}")

        common_cals = sorted(set(old_cals) & set(new_cals))
        any_cal_change = False
        for caliber in common_cals:
            added_k, removed_k, changed_t = diff_json_objects(
                old_cals[caliber], new_cals[caliber]
            )
            if added_k or removed_k or changed_t:
                if not any_cal_change:
                    print(f"    CHANGED:")
                    any_cal_change = True
                print(f"      ~ {caliber}")
                for k in added_k:
                    print(f"          + {k}: {new_cals[caliber][k]!r}")
                for k in removed_k:
                    print(f"          - {k}: {old_cals[caliber][k]!r}")
                for k, ov, nv in changed_t:
                    print(f"          {k}: {ov!r} -> {nv!r}")

        if not cal_added and not cal_removed and not any_cal_change:
            print("    (no changes)")


def main(argv: list[str] | None = None) -> None:
    """Entry point when run as a script.

    Args:
        argv: Argument list; defaults to sys.argv[1:].
    """
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print(f"Usage: {sys.argv[0]} <old_dir> <new_dir>", file=sys.stderr)
        sys.exit(1)

    old_dir, new_dir = args
    diff_json_files(old_dir, new_dir)


if __name__ == "__main__":
    main()
