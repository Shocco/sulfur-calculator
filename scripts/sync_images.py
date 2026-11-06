"""
Copy item images from a wikiteam3 image dump into public/images/.

The frontend expects:
    images/weapons/<weapon.image>          e.g. Ploika_Compact.png   (underscores)
    images/oils/<oil.name>.png             e.g. Action Oil.png       (spaces)
    images/scrolls/<scroll.name>.png       e.g. Scroll of Charm.png  (spaces)
    images/attachments/<basename(image)>   e.g. A12C_Muzzle_Brake.png (underscores)

The wiki dump stores files with underscores (MediaWiki file names), so each
target is looked up by its underscored name, case-insensitively on the first
letter, and copied in if it is missing or differs.

Usage:
    python -m scripts.sync_images <dump_images_dir> [--data-dir public/data] [--images-dir public/images]
"""

import argparse
import filecmp
import json
import os
import shutil
import sys
from typing import Dict, List, Tuple

ATTACHMENT_FILES = [
    'attachments-muzzle.json', 'attachments-sights.json', 'attachments-lasers.json',
    'attachments-chamber.json', 'attachments-chisels.json', 'attachments-insurance.json',
]


def wiki_filename(name: str) -> str:
    """MediaWiki file name: spaces become underscores, first letter uppercase."""
    name = name.replace(' ', '_')
    return name[:1].upper() + name[1:]


def _load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def wanted_images(data_dir: str) -> List[Tuple[str, str]]:
    """Return (category, target_filename) for every image the app references."""
    wanted = []
    for w in _load(os.path.join(data_dir, 'weapons.json')):
        if w.get('image'):
            wanted.append(('weapons', w['image']))
    for e in _load(os.path.join(data_dir, 'enchantments.json')):
        if e.get('name'):
            wanted.append(('oils', f"{e['name']}.png"))
    for s in _load(os.path.join(data_dir, 'scrolls.json')):
        if s.get('name'):
            wanted.append(('scrolls', f"{s['name']}.png"))
    for fname in ATTACHMENT_FILES:
        for a in _load(os.path.join(data_dir, fname)):
            if a.get('image'):
                wanted.append(('attachments', os.path.basename(a['image'])))
    # de-duplicate, keep order
    seen = set()
    return [x for x in wanted if not (x in seen or seen.add(x))]


def sync_images(dump_images_dir: str, data_dir: str, images_dir: str) -> Dict[str, list]:
    """Copy images from the dump into images_dir. Returns a report dict."""
    available = {f.lower(): f for f in os.listdir(dump_images_dir)}
    report = {'added': [], 'updated': [], 'unchanged': [], 'missing': []}

    for category, target in wanted_images(data_dir):
        src_name = available.get(wiki_filename(target).lower())
        dest = os.path.join(images_dir, category, target)
        if not src_name:
            if not os.path.exists(dest):
                report['missing'].append(f'{category}/{target}')
            else:
                report['unchanged'].append(f'{category}/{target}')
            continue
        src = os.path.join(dump_images_dir, src_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if not os.path.exists(dest):
            shutil.copy2(src, dest)
            report['added'].append(f'{category}/{target}')
        elif not filecmp.cmp(src, dest, shallow=False):
            shutil.copy2(src, dest)
            report['updated'].append(f'{category}/{target}')
        else:
            report['unchanged'].append(f'{category}/{target}')
    return report


def main():
    parser = argparse.ArgumentParser(description='Sync item images from a wiki image dump')
    parser.add_argument('dump_images_dir', help='The images/ folder of a wikiteam3 --images dump')
    parser.add_argument('--data-dir', default='public/data')
    parser.add_argument('--images-dir', default='public/images')
    args = parser.parse_args()

    if not os.path.isdir(args.dump_images_dir):
        print(f'Error: image dump folder not found: {args.dump_images_dir}')
        sys.exit(1)

    report = sync_images(args.dump_images_dir, args.data_dir, args.images_dir)
    print(f"Images: {len(report['added'])} added, {len(report['updated'])} updated, "
          f"{len(report['unchanged'])} unchanged, {len(report['missing'])} missing")
    for key in ('added', 'updated', 'missing'):
        for item in report[key]:
            print(f'  {key}: {item}')


if __name__ == '__main__':
    main()
