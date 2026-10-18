from core.catalog import CURATED_PACKAGES, search_catalog


def test_catalog_has_entries():
    assert len(CURATED_PACKAGES) >= 20


def test_catalog_search():
    results = search_catalog("git")
    assert any(r.name == "Git" for r in results)

    dev_tools = search_catalog("", category="Development")
    assert len(dev_tools) > 0
    assert all(r.category == "Development" for r in dev_tools)

