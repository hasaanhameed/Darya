import datetime as dt

from app.ingest.glofas.request_builder import AREA, CONSOLIDATED_END, SYSTEM_VERSION, plan_downloads


def test_whole_year_is_one_request():
    downloads = plan_downloads(dt.date(2015, 1, 1), dt.date(2015, 12, 31))

    assert len(downloads) == 1
    request = downloads[0].request
    assert request["year"] == ["2015"]
    assert request["month"] == [f"{m:02d}" for m in range(1, 13)]
    assert request["day"] == [f"{d:02d}" for d in range(1, 32)]


def test_request_has_fixed_dataset_settings():
    request = plan_downloads(dt.date(2015, 1, 1), dt.date(2015, 12, 31))[0].request

    assert request["system_version"] == [SYSTEM_VERSION]
    assert request["hydrological_model"] == ["lisflood"]
    assert request["timespan"] == ["time_mean"]
    assert request["variable"] == ["average_river_discharge_in_the_last_24_hours"]
    assert request["data_format"] == "netcdf"
    assert request["download_format"] == "unarchived"
    assert request["area"] == AREA


def test_partial_year_is_one_request_per_month_with_only_the_asked_days():
    downloads = plan_downloads(dt.date(2016, 1, 30), dt.date(2016, 2, 2))

    assert [d.request["month"] for d in downloads] == [["01"], ["02"]]
    assert [d.request["day"] for d in downloads] == [["30", "31"], ["01", "02"]]


def test_days_up_to_consolidated_end_are_consolidated_and_later_days_intermediate():
    start = CONSOLIDATED_END - dt.timedelta(days=1)
    end = CONSOLIDATED_END + dt.timedelta(days=2)

    downloads = plan_downloads(start, end)

    assert [(d.product_type, d.first_day, d.last_day) for d in downloads] == [
        ("consolidated", start, CONSOLIDATED_END),
        ("intermediate", CONSOLIDATED_END + dt.timedelta(days=1), end),
    ]
    assert [d.request["product_type"] for d in downloads] == [["consolidated"], ["intermediate"]]


def test_file_name_says_product_and_exact_days():
    downloads = plan_downloads(dt.date(2015, 1, 1), dt.date(2016, 1, 5))

    assert [d.file_name for d in downloads] == [
        "consolidated_2015-01-01_2015-12-31.nc",
        "consolidated_2016-01-01_2016-01-05.nc",
    ]
