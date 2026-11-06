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
