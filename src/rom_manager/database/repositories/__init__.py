"""Per-aggregate building blocks for the SQLite library repository.

``LibraryRepository`` (in :mod:`rom_manager.database.repository`) is assembled
from ``_RepositoryBase`` plus one mixin per aggregate:

- :class:`~rom_manager.database.repositories.games.GamesMixin`
- :class:`~rom_manager.database.repositories.metadata.MetadataMixin`
- :class:`~rom_manager.database.repositories.sync.SyncMixin`
- :class:`~rom_manager.database.repositories.assets.AssetsMixin`
- :class:`~rom_manager.database.repositories.duplicates.DuplicatesMixin`

Shared dataclasses live in :mod:`rom_manager.database.repositories.models`.
"""
