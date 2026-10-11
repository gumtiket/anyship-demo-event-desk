import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

import httpx
import pytest

BASE = "http://127.0.0.1:18093"


@pytest.fixture(scope="session", autouse=True)
def configure_target(pytestconfig):
    global BASE
    BASE = pytestconfig.getoption("--base-url")
    if urlsplit(BASE).hostname not in {"localhost", "127.0.0.1"}:
        raise RuntimeError("Run write tests only against a disposable local demo.")


def request(method, path, **kwargs):
    return httpx.request(method, BASE + path, timeout=15, **kwargs)


def nickname():
    return "가상 참가자 " + uuid.uuid4().hex[:8]


def test_health_and_seeded_events():
    assert request("GET", "/healthz").status_code == 200
    assert "모여봐요" in request("GET", "/").text
    events = request("GET", "/api/events").json()
    assert len(events) == 3
    assert all(event["remaining"] == event["capacity"] - event["occupied"] for event in events)


def test_join_duplicate_cancel_and_repeat_cancel():
    name = nickname()
    before = request("GET", "/api/events").json()[0]
    joined = request(
        "POST", "/api/registrations", json={"event_id": before["id"], "nickname": name}
    )
    assert joined.status_code == 201
    record = joined.json()
    assert len(record["receipt"]) == 24
    assert request("GET", "/api/events").json()[0]["occupied"] == before["occupied"] + 1
    assert (
        request(
            "POST", "/api/registrations", json={"event_id": before["id"], "nickname": name}
        ).status_code
        == 409
    )
    path = f"/api/registrations/{record['id']}/cancel"
    assert request("POST", path, json={"receipt": "0" * 24}).status_code == 403
    assert request("POST", path, json={"receipt": record["receipt"]}).status_code == 200
    assert request("POST", path, json={"receipt": record["receipt"]}).status_code == 409
    assert request("GET", "/api/events").json()[0]["occupied"] == before["occupied"]


@pytest.mark.parametrize(
    "body",
    [
        {"event_id": True, "nickname": "A"},
        {"event_id": "1", "nickname": "A"},
        {"event_id": 1, "nickname": " "},
        {"event_id": 1, "nickname": "x" * 41},
    ],
)
def test_invalid_inputs(body):
    assert request("POST", "/api/registrations", json=body).status_code == 422


def test_missing_event_and_record():
    assert (
        request(
            "POST", "/api/registrations", json={"event_id": 2147483647, "nickname": nickname()}
        ).status_code
        == 404
    )
    assert (
        request(
            "POST", "/api/registrations/2147483647/cancel", json={"receipt": "0" * 24}
        ).status_code
        == 404
    )


def test_concurrent_capacity_and_cancellation():
    event = request("GET", "/api/events").json()[2]
    remaining = event["remaining"]
    assert remaining > 0

    def join(_):
        return request(
            "POST", "/api/registrations", json={"event_id": event["id"], "nickname": nickname()}
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(join, range(8)))
    assert sum(result.status_code == 201 for result in results) == remaining
    assert sum(result.status_code == 409 for result in results) == 8 - remaining
    assert request("GET", "/api/events").json()[2]["remaining"] == 0
    records = [result.json() for result in results if result.status_code == 201]
    record = records[0]
    with ThreadPoolExecutor(max_workers=2) as executor:
        cancelled = list(
            executor.map(
                lambda _: request(
                    "POST",
                    f"/api/registrations/{record['id']}/cancel",
                    json={"receipt": record["receipt"]},
                ),
                range(2),
            )
        )
    assert sorted(result.status_code for result in cancelled) == [200, 409]
    for record in records[1:]:
        assert (
            request(
                "POST",
                f"/api/registrations/{record['id']}/cancel",
                json={"receipt": record["receipt"]},
            ).status_code
            == 200
        )
    assert request("GET", "/api/events").json()[2]["remaining"] == remaining


def test_html_looking_nickname_remains_data():
    name = "<b>가상 참가자</b>" + uuid.uuid4().hex[:4]
    response = request("POST", "/api/registrations", json={"event_id": 2, "nickname": name})
    assert response.status_code == 201 and response.json()["nickname"] == name
    record = response.json()
    assert (
        request(
            "POST", f"/api/registrations/{record['id']}/cancel", json={"receipt": record["receipt"]}
        ).status_code
        == 200
    )
