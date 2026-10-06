"""Dry runs must not reset (remove) the checked tags when all media is already tagged."""

import copy
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import renameinatorr, upgradinatorr

CHECKED_TAG = 1
IGNORE_TAG = 2


class SilentLogger:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class FakeArr:
    """Minimal in-memory Radarr client recording every write call."""

    instance_name = "Movies"
    instance_type = "Radarr"

    def __init__(self, media):
        self.media = media
        self.removed_tags = []
        self.added_tags = []
        self.searched = []
        self.renamed = []

    def get_parsed_media(self, include_episode=False):
        return copy.deepcopy(self.media)

    def get_tag_id_from_name(self, name):
        return {"checked": CHECKED_TAG, "ignore": IGNORE_TAG}[name]

    def remove_tags(self, media_ids, tag_id):
        self.removed_tags.append((media_ids, tag_id))
        for item in self.media:
            if item["media_id"] in media_ids:
                item["tags"] = [tag for tag in item["tags"] if tag != tag_id]

    def add_tags(self, media_ids, tag_id):
        self.added_tags.append((media_ids, tag_id))

    def search_media(self, media_id):
        self.searched.append(media_id)
        return {"id": 100 + media_id}

    def wait_for_command(self, command_id):
        return True

    def get_queue(self):
        return {"records": []}

    def get_rename_list(self, media_id):
        return []

    def rename_media(self, media_ids):
        self.renamed.append(media_ids)


def movie(media_id, tags):
    return {
        "media_id": media_id,
        "title": f"Movie {media_id}",
        "year": 2020,
        "tags": tags,
        "monitored": True,
        "status": "released",
        "seasons": None,
        "path_name": f"Movie {media_id} (2020)",
        "root_folder": "/movies",
    }


def all_tagged():
    return [movie(1, [CHECKED_TAG]), movie(2, [CHECKED_TAG])]


# ─── Upgradinatorr ─────────────────────────────────────────────

UPGRADINATORR_SETTINGS = {
    "instance": "Movies",
    "count": 1,
    "tag_name": "checked",
    "ignore_tag": "ignore",
    "unattended": True,
}


def test_upgradinatorr_dry_run_keeps_tags():
    app = FakeArr(all_tagged())
    output = upgradinatorr.process_instance(
        "radarr", UPGRADINATORR_SETTINGS, app, SilentLogger(), SimpleNamespace(dry_run=True)
    )

    assert app.removed_tags == []
    assert app.added_tags == [] and app.searched == []
    # The simulated reset still shows what the next cycle would search
    assert [item["media_id"] for item in output["data"]] == [1]


def test_upgradinatorr_unattended_resets_tags():
    app = FakeArr(all_tagged())
    upgradinatorr.process_instance(
        "radarr", UPGRADINATORR_SETTINGS, app, SilentLogger(), SimpleNamespace(dry_run=False)
    )

    assert app.removed_tags == [([1, 2], CHECKED_TAG)]
    assert app.searched == [1]
    assert app.added_tags == [(1, CHECKED_TAG)]


# ─── Renameinatorr ─────────────────────────────────────────────

def renameinatorr_config(dry_run):
    return SimpleNamespace(
        dry_run=dry_run,
        count=0,
        tag_name="checked",
        ignore_tag="ignore",
        enable_batching=False,
        rename_folders=False,
    )


def test_renameinatorr_dry_run_keeps_tags():
    app = FakeArr(all_tagged())
    output = renameinatorr.process_instance(app, "radarr", renameinatorr_config(True), SilentLogger())

    assert app.removed_tags == []
    assert app.renamed == [] and app.added_tags == []
    assert sorted(item["title"] for item in output) == ["Movie 1", "Movie 2"]


def test_renameinatorr_resets_tags():
    app = FakeArr(all_tagged())
    renameinatorr.process_instance(app, "radarr", renameinatorr_config(False), SilentLogger())

    assert app.removed_tags == [([1, 2], CHECKED_TAG)]
    assert app.renamed == [[1, 2]]
    assert app.added_tags == [([1, 2], CHECKED_TAG)]
