from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_table_map_has_search_status_zone_filters_and_counters():
    source = read('alrajhi_client/views/restaurant/table_map_widget.py')
    assert 'restaurantTableSearchInput' in source
    assert 'restaurantTableStatusFilter' in source
    assert 'restaurantTableZoneFilter' in source
    assert '_STATUS_FILTERS = ("all", "free", "occupied", "kitchen", "ready", "payment", "reserved")' in source
    assert 'counter_labels' in source
    assert '_matches_filters' in source
    assert '_zone_name' in source


def test_table_map_filter_translations_exist_for_all_languages():
    source = read('alrajhi_client/i18n/translator.py')
    for key in (
        'restaurant.table_search_placeholder',
        'restaurant.filter.all_statuses',
        'restaurant.filter.all_zones',
        'restaurant.table_filter_empty',
    ):
        assert source.count(key) >= 3


def test_table_map_filter_controls_are_styled():
    qss = read('alrajhi_client/theme/qss.py')
    for selector in (
        'restaurantTableFilterBar',
        'restaurantTableCounterBar',
        'restaurantTableSearchInput',
        'restaurantTableStatusFilter',
        'restaurantTableZoneFilter',
        'restaurantTableEmptyLabel',
    ):
        assert selector in qss
