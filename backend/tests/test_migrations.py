"""Migration graph sanity.

A second head means `alembic upgrade head` fails at deploy with "Multiple
head revisions are present", and nothing else here would catch it: the
conftest fixture upgrades a fresh database, which succeeds right up until
two migrations actually share a parent.

The revisions are parsed straight from the files rather than through
alembic's Python API on purpose -- `backend/alembic/` is the migrations
directory, so it shadows the installed `alembic` package once the test
suite's rootdir is on sys.path, and `import alembic.config` fails.
"""

import re
from pathlib import Path

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"

_REVISION = re.compile(r'^revision\s*=\s*["\']([^"\']+)["\']', re.M)
_DOWN = re.compile(r'^down_revision\s*=\s*["\']([^"\']+)["\']', re.M)


def _migrations() -> dict[str, tuple[str, str | None]]:
    """revision -> (filename stem, down_revision)."""
    found = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        match = _REVISION.search(text)
        assert match, f"{path.name} declares no revision"
        down = _DOWN.search(text)
        found[match.group(1)] = (path.stem, down.group(1) if down else None)
    return found


def test_migrations_are_present():
    # Guards the glob itself: an empty directory would make every other
    # assertion here vacuously true.
    assert len(_migrations()) > 50


def test_there_is_exactly_one_head():
    migrations = _migrations()
    parents = {down for _, down in migrations.values() if down}
    heads = sorted(set(migrations) - parents)
    assert len(heads) == 1, (
        f"{len(heads)} migration heads: {heads}. Two migrations share a "
        "down_revision; re-parent the newer one onto the other."
    )


def test_every_down_revision_exists():
    migrations = _migrations()
    dangling = {
        rev: down for rev, (_, down) in migrations.items()
        if down and down not in migrations
    }
    assert not dangling, f"migrations pointing at missing parents: {dangling}"


def test_exactly_one_base_revision():
    migrations = _migrations()
    bases = sorted(rev for rev, (_, down) in migrations.items() if down is None)
    assert len(bases) == 1, f"expected one base migration, found {bases}"


def test_the_chain_reaches_every_migration():
    migrations = _migrations()
    parents = {down for _, down in migrations.values() if down}
    head = (set(migrations) - parents).pop()

    seen = set()
    cursor: str | None = head
    while cursor is not None:
        assert cursor not in seen, f"cycle in migration chain at {cursor}"
        seen.add(cursor)
        cursor = migrations[cursor][1]

    assert seen == set(migrations), (
        f"unreachable migrations: {sorted(set(migrations) - seen)}"
    )


def test_revision_ids_share_their_filename_number():
    """Every revision begins with its file's numeric prefix.

    Deliberately weaker than "revision == filename stem", which CLAUDE.md
    documents and which the newer migrations follow: 0001-0025 predate that
    and use a bare number (revision "0001" in 0001_initial_schema.py). Both
    styles are in the tree and neither is worth rewriting, since changing a
    revision id would break every deployed alembic_version row. What has to
    hold either way is that a file's number identifies its revision, which
    is what makes the on-disk ordering trustworthy.
    """
    mismatched = {
        rev: stem
        for rev, (stem, _) in _migrations().items()
        if not rev.startswith(stem.split("_", 1)[0])
    }
    assert not mismatched, f"revision/filename number mismatches: {mismatched}"
