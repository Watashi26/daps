"""In-memory stand-ins for ARR clients used by module tests."""

import copy

CHECKED_TAG = 1
IGNORE_TAG = 2
USE_TAG = 3

TAGS = [
    {"id": CHECKED_TAG, "label": "checked"},
    {"id": IGNORE_TAG, "label": "ignore"},
    {"id": USE_TAG, "label": "4k"},
]


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

    def get_all_tags(self):
        return copy.deepcopy(TAGS)

    def get_tag_id_from_name(self, name):
        return next(tag["id"] for tag in TAGS if tag["label"] == name.lower())

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
