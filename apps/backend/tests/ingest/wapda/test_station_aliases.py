from app.ingest.wapda.station_aliases import station_id_for


def test_maps_ghazi_barotha_spellings():
    assert station_id_for("GHAZI BAROTHA") == "ghazi_barotha"
    assert station_id_for("G/BAROTHA") == "ghazi_barotha"


def test_maps_t4_with_and_without_colon():
    assert station_id_for("T-4 EXT:") == "tarbela_t4"
    assert station_id_for("T-4 EXT") == "tarbela_t4"


def test_ignores_case_and_surrounding_spaces():
    assert station_id_for("  Tarbela ") == "tarbela"


def test_ignores_gomal_zam():
    assert station_id_for("GOMAL ZAM") is None


def test_ignores_unknown_names():
    assert station_id_for("8.7") is None
    assert station_id_for("POWER STATIONS") is None
