"""Tests for scripts/diff_data.py - JSON diff utility for SULFUR calculator data."""

from __future__ import annotations

from typing import Any

import pytest

from scripts.diff_data import diff_json_arrays, diff_json_objects


# ---------------------------------------------------------------------------
# diff_json_arrays
# ---------------------------------------------------------------------------


class TestDiffJsonArraysAdded:
    """Items present in new but absent in old."""

    def test_single_item_added(self) -> None:
        old: list[dict[str, Any]] = [{"name": "Alpha", "damage": 10}]
        new: list[dict[str, Any]] = [
            {"name": "Alpha", "damage": 10},
            {"name": "Beta", "damage": 20},
        ]
        added, removed, changed = diff_json_arrays(old, new)
        assert added == ["Beta"]
        assert removed == []
        assert changed == []

    def test_multiple_items_added_sorted(self) -> None:
        old: list[dict[str, Any]] = []
        new: list[dict[str, Any]] = [
            {"name": "Zeta", "damage": 5},
            {"name": "Alpha", "damage": 3},
        ]
        added, removed, changed = diff_json_arrays(old, new)
        assert added == ["Alpha", "Zeta"]
        assert removed == []
        assert changed == []

    def test_all_items_new(self) -> None:
        old: list[dict[str, Any]] = []
        new: list[dict[str, Any]] = [{"name": "X"}, {"name": "Y"}]
        added, removed, changed = diff_json_arrays(old, new)
        assert set(added) == {"X", "Y"}
        assert removed == []
        assert changed == []


class TestDiffJsonArraysRemoved:
    """Items present in old but absent in new."""

    def test_single_item_removed(self) -> None:
        old: list[dict[str, Any]] = [
            {"name": "Alpha"},
            {"name": "Beta"},
        ]
        new: list[dict[str, Any]] = [{"name": "Alpha"}]
        added, removed, changed = diff_json_arrays(old, new)
        assert added == []
        assert removed == ["Beta"]
        assert changed == []

    def test_multiple_items_removed_sorted(self) -> None:
        old: list[dict[str, Any]] = [
            {"name": "Zeta"},
            {"name": "Alpha"},
            {"name": "Mu"},
        ]
        new: list[dict[str, Any]] = []
        added, removed, changed = diff_json_arrays(old, new)
        assert added == []
        assert removed == ["Alpha", "Mu", "Zeta"]
        assert changed == []

    def test_all_items_removed(self) -> None:
        old: list[dict[str, Any]] = [{"name": "A"}, {"name": "B"}]
        new: list[dict[str, Any]] = []
        added, removed, changed = diff_json_arrays(old, new)
        assert added == []
        assert set(removed) == {"A", "B"}
        assert changed == []


class TestDiffJsonArraysChanged:
    """Items that exist in both but have differing field values."""

    def test_single_field_changed(self) -> None:
        old: list[dict[str, Any]] = [{"name": "Alpha", "damage": 10}]
        new: list[dict[str, Any]] = [{"name": "Alpha", "damage": 15}]
        added, removed, changed = diff_json_arrays(old, new)
        assert added == []
        assert removed == []
        assert len(changed) == 1
        name, field_diffs = changed[0]
        assert name == "Alpha"
        assert field_diffs == {"damage": (10, 15)}

    def test_multiple_fields_changed(self) -> None:
        old: list[dict[str, Any]] = [{"name": "Gun", "damage": 50, "recoil": 5, "spread": 2}]
        new: list[dict[str, Any]] = [{"name": "Gun", "damage": 60, "recoil": 3, "spread": 2}]
        added, removed, changed = diff_json_arrays(old, new)
        assert len(changed) == 1
        name, field_diffs = changed[0]
        assert name == "Gun"
        assert field_diffs["damage"] == (50, 60)
        assert field_diffs["recoil"] == (5, 3)
        assert "spread" not in field_diffs

    def test_field_added_to_item(self) -> None:
        old: list[dict[str, Any]] = [{"name": "Alpha"}]
        new: list[dict[str, Any]] = [{"name": "Alpha", "damage": 10}]
        added, removed, changed = diff_json_arrays(old, new)
        assert len(changed) == 1
        _, field_diffs = changed[0]
        assert field_diffs == {"damage": (None, 10)}

    def test_field_removed_from_item(self) -> None:
        old: list[dict[str, Any]] = [{"name": "Alpha", "damage": 10}]
        new: list[dict[str, Any]] = [{"name": "Alpha"}]
        added, removed, changed = diff_json_arrays(old, new)
        assert len(changed) == 1
        _, field_diffs = changed[0]
        assert field_diffs == {"damage": (10, None)}

    def test_no_changes_when_identical(self) -> None:
        items: list[dict[str, Any]] = [
            {"name": "Alpha", "damage": 10},
            {"name": "Beta", "damage": 20},
        ]
        added, removed, changed = diff_json_arrays(items, items)
        assert added == []
        assert removed == []
        assert changed == []

    def test_custom_key_field(self) -> None:
        old: list[dict[str, Any]] = [{"id": "a1", "value": 100}]
        new: list[dict[str, Any]] = [{"id": "a1", "value": 200}]
        added, removed, changed = diff_json_arrays(old, new, key="id")
        assert len(changed) == 1
        name, field_diffs = changed[0]
        assert name == "a1"
        assert field_diffs["value"] == (100, 200)

    def test_mixed_add_remove_change(self) -> None:
        old: list[dict[str, Any]] = [
            {"name": "Alpha", "dmg": 10},
            {"name": "Beta", "dmg": 20},
        ]
        new: list[dict[str, Any]] = [
            {"name": "Alpha", "dmg": 15},
            {"name": "Gamma", "dmg": 30},
        ]
        added, removed, changed = diff_json_arrays(old, new)
        assert added == ["Gamma"]
        assert removed == ["Beta"]
        assert len(changed) == 1
        assert changed[0][0] == "Alpha"
        assert changed[0][1] == {"dmg": (10, 15)}


# ---------------------------------------------------------------------------
# diff_json_objects
# ---------------------------------------------------------------------------


class TestDiffJsonObjectsAdded:
    """Keys present in new but absent in old."""

    def test_single_key_added(self) -> None:
        old: dict[str, Any] = {"a": 1}
        new: dict[str, Any] = {"a": 1, "b": 2}
        added, removed, changed = diff_json_objects(old, new)
        assert added == ["b"]
        assert removed == []
        assert changed == []

    def test_multiple_keys_added_sorted(self) -> None:
        old: dict[str, Any] = {}
        new: dict[str, Any] = {"z": 26, "a": 1, "m": 13}
        added, removed, changed = diff_json_objects(old, new)
        assert added == ["a", "m", "z"]
        assert removed == []
        assert changed == []


class TestDiffJsonObjectsRemoved:
    """Keys present in old but absent in new."""

    def test_single_key_removed(self) -> None:
        old: dict[str, Any] = {"a": 1, "b": 2}
        new: dict[str, Any] = {"a": 1}
        added, removed, changed = diff_json_objects(old, new)
        assert added == []
        assert removed == ["b"]
        assert changed == []

    def test_multiple_keys_removed_sorted(self) -> None:
        old: dict[str, Any] = {"z": 26, "a": 1, "m": 13}
        new: dict[str, Any] = {}
        added, removed, changed = diff_json_objects(old, new)
        assert added == []
        assert removed == ["a", "m", "z"]
        assert changed == []


class TestDiffJsonObjectsChanged:
    """Keys that exist in both dicts but with different values."""

    def test_single_value_changed(self) -> None:
        old: dict[str, Any] = {"damage": 60}
        new: dict[str, Any] = {"damage": 80}
        added, removed, changed = diff_json_objects(old, new)
        assert added == []
        assert removed == []
        assert changed == [("damage", 60, 80)]

    def test_multiple_values_changed_sorted_by_key(self) -> None:
        old: dict[str, Any] = {"recoil": 5, "spread": 2, "damage": 60}
        new: dict[str, Any] = {"recoil": 3, "spread": 4, "damage": 60}
        added, removed, changed = diff_json_objects(old, new)
        assert added == []
        assert removed == []
        keys_changed = [k for k, _, _ in changed]
        assert keys_changed == sorted(keys_changed)
        assert ("recoil", 5, 3) in changed
        assert ("spread", 2, 4) in changed
        assert all(k != "damage" for k, _, _ in changed)

    def test_value_type_change(self) -> None:
        old: dict[str, Any] = {"count": 1}
        new: dict[str, Any] = {"count": "1"}
        added, removed, changed = diff_json_objects(old, new)
        assert changed == [("count", 1, "1")]

    def test_no_changes_when_identical(self) -> None:
        data: dict[str, Any] = {"a": 1, "b": 2}
        added, removed, changed = diff_json_objects(data, data)
        assert added == []
        assert removed == []
        assert changed == []

    def test_mixed_add_remove_change(self) -> None:
        old: dict[str, Any] = {"a": 1, "b": 2, "c": 3}
        new: dict[str, Any] = {"a": 99, "c": 3, "d": 4}
        added, removed, changed = diff_json_objects(old, new)
        assert added == ["d"]
        assert removed == ["b"]
        assert changed == [("a", 1, 99)]

    def test_nested_value_treated_as_opaque(self) -> None:
        """Nested dicts are compared by equality, not recursively."""
        old: dict[str, Any] = {"stats": {"hp": 100, "mp": 50}}
        new: dict[str, Any] = {"stats": {"hp": 200, "mp": 50}}
        added, removed, changed = diff_json_objects(old, new)
        assert changed == [("stats", {"hp": 100, "mp": 50}, {"hp": 200, "mp": 50})]
