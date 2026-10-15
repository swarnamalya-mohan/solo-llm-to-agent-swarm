from agents.workflow import check_timeline

def test_inverted_events():
    events = [{"time": "04:00", "event": "arrived"}, {"time": "03:30", "event": "departed"}]
    result = check_timeline({"events": events})
    assert result["status"] == "contradiction"
    assert len(result["inversions"]) == 1

def test_consistent_events():
    assert check_timeline({"events": [{"time":"03:00"},{"time":"04:00"}]})["status"] == "consistent"

def test_invalid_event():
    assert check_timeline({"events": [{"time": "25:00"}]})["status"] == "unknown"
