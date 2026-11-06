import json
import os

from scripts.sync_images import sync_images, wiki_filename


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def test_wiki_filename():
    assert wiki_filename('Action Oil.png') == 'Action_Oil.png'
    assert wiki_filename('scroll of Charm.png') == 'Scroll_of_Charm.png'


def test_sync_images_maps_names_and_reports(tmp_path):
    dump = tmp_path / 'dump'
    dump.mkdir()
    for name in ['Ploika_Compact.png', 'Action_Oil.png', 'Scroll_of_Charm.png', 'A12C_Muzzle_Brake.png']:
        (dump / name).write_bytes(name.encode())

    data = tmp_path / 'data'
    _write(str(data / 'weapons.json'), [{'name': 'Ploika Compact', 'image': 'Ploika_Compact.png'}])
    _write(str(data / 'enchantments.json'), [{'name': 'Action Oil'}, {'name': 'Ghost Oil'}])
    _write(str(data / 'scrolls.json'), [{'name': 'Scroll of Charm'}])
    _write(str(data / 'attachments-muzzle.json'),
           [{'name': 'A12C Muzzle Brake', 'image': '/images/attachments/A12C_Muzzle_Brake.png'}])

    images = tmp_path / 'images'
    (images / 'scrolls').mkdir(parents=True)
    (images / 'scrolls' / 'Scroll of Charm.png').write_bytes(b'old')

    report = sync_images(str(dump), str(data), str(images))

    assert (images / 'weapons' / 'Ploika_Compact.png').exists()
    assert (images / 'oils' / 'Action Oil.png').read_bytes() == b'Action_Oil.png'
    assert (images / 'attachments' / 'A12C_Muzzle_Brake.png').exists()
    assert 'scrolls/Scroll of Charm.png' in report['updated']
    assert 'oils/Ghost Oil.png' in report['missing']
    assert len(report['added']) == 3

    # second run is a no-op
    report2 = sync_images(str(dump), str(data), str(images))
    assert not report2['added'] and not report2['updated']
