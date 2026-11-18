from datetime import date


def _all_yes(version, qid_offset=0):
    responses = []
    for sec in version["sections"]:
        for q in sec["questions"]:
            responses.append(
                {
                    "question_id": q["id"],
                    "response_value": "Yes",
                    "comment": None,
                }
            )
    return responses


def test_submit_search_and_detail(client):
    versions = client.get("/api/v1/questionnaires/latest").json()
    assert len(versions) == 1
    version = versions[0]
    full = client.get(f"/api/v1/questionnaires/versions/{version['id']}").json()

    payload = {
        "case_id": "CASE-1001",
        "audit_date": str(date.today()),
        "auditor": "Alice",
        "tse": "Bob",
        "customer": "Acme",
        "case_priority": "P2",
        "customer_tier": "Standard",
        "questionnaire_version_id": full["id"],
        "responses": [
            {"question_id": q["id"], "response_value": "Yes", "comment": None}
            for sec in full["sections"]
            for q in sec["questions"]
        ],
    }
    r = client.post("/api/v1/audits", json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["total_score"] == 75

    dup = client.post("/api/v1/audits", json=payload)
    assert dup.status_code == 409

    search = client.get("/api/v1/audits?case_id=1001&page_size=25").json()
    assert search["total"] >= 1
    assert search["items"][0]["case_id"] == "CASE-1001"

    detail = client.get(f"/api/v1/audits/{created['id']}").json()
    assert len(detail["responses"]) == 15