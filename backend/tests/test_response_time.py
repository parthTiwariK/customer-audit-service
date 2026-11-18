def test_x_response_time_header(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "x-response-time" in {k.lower() for k in r.headers}