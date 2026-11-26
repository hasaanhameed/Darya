import datetime as dt

from app.ingest.imerg.request_builder import BBOX, IMERG_COLLECTION_ID, build_request, split_into_months


def test_splits_a_range_into_calendar_months():
    months = split_into_months(dt.date(2022, 7, 30), dt.date(2022, 9, 2))

    assert months == [
        (dt.date(2022, 7, 30), dt.date(2022, 7, 31)),
        (dt.date(2022, 8, 1), dt.date(2022, 8, 31)),
        (dt.date(2022, 9, 1), dt.date(2022, 9, 2)),
    ]


def test_request_asks_for_our_area_and_only_the_precipitation_variable():
    request = build_request(dt.date(2022, 8, 1), dt.date(2022, 8, 31))

    assert request.collection.id == IMERG_COLLECTION_ID
    assert (request.spatial.w, request.spatial.s, request.spatial.e, request.spatial.n) == BBOX
    assert request.variables == ["precipitation"]
    assert request.is_valid()


def test_request_covers_whole_utc_days():
    request = build_request(dt.date(2022, 8, 1), dt.date(2022, 8, 31))

    assert request.temporal == {
        "start": dt.datetime(2022, 8, 1, 0, 0, 0, tzinfo=dt.UTC),
        "stop": dt.datetime(2022, 8, 31, 23, 59, 59, tzinfo=dt.UTC),
    }
