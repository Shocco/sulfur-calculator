"""Integration test: update_all.main() extract + merge on a tiny dump."""
import json
import sys

from scripts import update_all

PAGE = '<page><title>{t}</title><revision><text xml:space="preserve">{x}</text></revision></page>'


def _dump(tmp_path):
    pages = [
        PAGE.format(t='Priming Bolt', x=(
            '{{Item Infobox\n| kind = attachment\n'
            '| SubType = [[Chamber Attachments|Chamber attachments]]\n| Spread = -1.5\n}}')),
        PAGE.format(t='Time Arrow Oil', x='{{Item Infobox\n| kind = oil\n| Damage = +10%\n}}'),
        PAGE.format(t='Arrow Oil', x='#REDIRECT [[Time Arrow Oil]]'),
    ]
    p = tmp_path / 'dump.xml'
    p.write_text('<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">'
                 + ''.join(pages) + '</mediawiki>', encoding='utf-8')
    return p


def test_merge_drops_renamed_and_moved_items(tmp_path, monkeypatch):
    old = tmp_path / 'old'
    old.mkdir()
    (old / 'enchantments.json').write_text(json.dumps(
        [{'name': 'Arrow Oil', 'modifiers': []}, {'name': 'Stub Oil', 'modifiers': []}]))
    (old / 'attachments-insurance.json').write_text(json.dumps(
        [{'name': 'Priming Bolt', 'type': 'insurance', 'modifiers': {}}]))
    out = tmp_path / 'out'
    out.mkdir()

    monkeypatch.setattr(sys, 'argv', ['update_all', str(_dump(tmp_path)),
                                      '--output-dir', str(out), '--old-dir', str(old)])
    update_all.main()

    oils = {o['name'] for o in json.load(open(out / 'enchantments.json'))}
    assert 'Time Arrow Oil' in oils and 'Stub Oil' in oils
    assert 'Arrow Oil' not in oils
    chamber = {a['name'] for a in json.load(open(out / 'attachments-chamber.json'))}
    insurance = {a['name'] for a in json.load(open(out / 'attachments-insurance.json'))}
    assert 'Priming Bolt' in chamber
    assert 'Priming Bolt' not in insurance


class TestFillSlotsFromSpecificAttachments:
    """Weapons the wiki lists no attachment slots for fall back to the slots
    implied by their (curated) specificAttachments."""

    SLOT_BY_NAME = {
        "Laser Sight (Red)": "laser",
        "Sniper Scope": "sight",
        "Gun Crank": "chamber",
        "Insurance": "insurance",
    }

    def test_weapon_with_only_insurance_gains_slots_of_its_specific_attachments(self):
        from scripts.update_all import _fill_slots_from_specific_attachments
        weapons = [{"name": "D4RT", "allowedAttachments": ["insurance"],
                    "specificAttachments": ["Laser Sight (Red)", "Sniper Scope", "Insurance"]}]
        _fill_slots_from_specific_attachments(weapons, self.SLOT_BY_NAME)
        assert weapons[0]["allowedAttachments"] == ["laser", "sight", "insurance"]

    def test_weapon_with_wiki_slots_is_left_alone(self):
        from scripts.update_all import _fill_slots_from_specific_attachments
        weapons = [{"name": "Breacher 8", "allowedAttachments": ["muzzle", "insurance"],
                    "specificAttachments": ["Gun Crank", "Sniper Scope"]}]
        _fill_slots_from_specific_attachments(weapons, self.SLOT_BY_NAME)
        assert weapons[0]["allowedAttachments"] == ["muzzle", "insurance"]

    def test_unknown_names_and_empty_lists_are_ignored(self):
        from scripts.update_all import _fill_slots_from_specific_attachments
        weapons = [{"name": "A", "allowedAttachments": ["insurance"], "specificAttachments": ["Muzzle", "Nope"]},
                   {"name": "B", "allowedAttachments": ["insurance"], "specificAttachments": []}]
        _fill_slots_from_specific_attachments(weapons, self.SLOT_BY_NAME)
        assert [w["allowedAttachments"] for w in weapons] == [["insurance"], ["insurance"]]


class TestApplyOverrides:
    """Hand-checked corrections for values where the wiki lags the game."""

    OVERRIDE = {
        "Scroll of Ice Beam": {
            "modifiers": {"Damage": {"wikiValue": -0.9, "value": -0.95}},
            "source": "1.0 patch notes",
        }
    }

    def _scrolls(self, damage):
        return [{"name": "Scroll of Ice Beam", "modifiers": [
            {"attribute": "RPM", "modType": 200, "value": 9.0},
            {"attribute": "Damage", "modType": 200, "value": damage},
        ]}]

    def test_override_replaces_the_stale_wiki_value(self):
        from scripts.update_all import _apply_overrides
        scrolls = self._scrolls(-0.9)
        notes = _apply_overrides(scrolls, self.OVERRIDE)
        assert scrolls[0]["modifiers"][1] == {"attribute": "Damage", "modType": 200, "value": -0.95}
        assert scrolls[0]["modifiers"][0]["value"] == 9.0
        assert len(notes) == 1 and "applied" in notes[0]

    def test_override_is_skipped_once_the_wiki_value_changes(self):
        from scripts.update_all import _apply_overrides
        scrolls = self._scrolls(-0.95)
        notes = _apply_overrides(scrolls, self.OVERRIDE)
        assert scrolls[0]["modifiers"][1]["value"] == -0.95
        assert len(notes) == 1 and "no longer needed" in notes[0]

    def test_override_is_skipped_when_the_wiki_moves_to_a_third_value(self):
        from scripts.update_all import _apply_overrides
        scrolls = self._scrolls(-0.8)
        notes = _apply_overrides(scrolls, self.OVERRIDE)
        assert scrolls[0]["modifiers"][1]["value"] == -0.8
        assert len(notes) == 1 and "not applied" in notes[0]

    def test_missing_item_or_attribute_is_reported_not_invented(self):
        from scripts.update_all import _apply_overrides
        scrolls = [{"name": "Scroll of Ice Beam", "modifiers": []}]
        notes = _apply_overrides(scrolls, {**self.OVERRIDE, "Scroll of Nothing": {"modifiers": {"Damage": {"wikiValue": 1, "value": 2}}}})
        assert scrolls == [{"name": "Scroll of Ice Beam", "modifiers": []}]
        assert len(notes) == 2 and all("not found" in n for n in notes)

    def test_shipped_overrides_file_is_well_formed(self):
        import json, os
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "data_overrides.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for filename, items in data.items():
            assert filename.endswith(".json")
            for name, entry in items.items():
                assert entry["source"], name
                for attribute, change in entry["modifiers"].items():
                    assert set(change) == {"wikiValue", "value"}, (name, attribute)
