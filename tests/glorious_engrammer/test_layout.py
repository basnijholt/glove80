from glove80 import build_layout as build_family_layout
from tests.assertions import assert_layout_equal


def test_glorious_engrammer_matches_release(load_glorious_engrammer_variant) -> None:
    expected = load_glorious_engrammer_variant("v42_rc6_preview")
    built = build_family_layout("glorious_engrammer", "v42_rc6_preview")
    assert_layout_equal(built, expected, label="glorious_engrammer:v42_rc6_preview")
