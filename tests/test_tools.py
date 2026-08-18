from strands_guardian.utils.haversine import haversine_km, bearing_degrees, bearing_label


def test_haversine_same_point():
    assert haversine_km(29.76, -95.37, 29.76, -95.37) < 0.01


def test_haversine_known_distance():
    # Houston to Atlanta is roughly 1200 km
    dist = haversine_km(29.76, -95.37, 33.75, -84.39)
    assert 1100 < dist < 1300


def test_bearing_north():
    b = bearing_degrees(30.0, -90.0, 35.0, -90.0)
    assert abs(b) < 1 or abs(b - 360) < 1
    assert bearing_label(b) == "N"


def test_bearing_east():
    b = bearing_degrees(30.0, -90.0, 30.0, -80.0)
    assert 85 < b < 95
    assert bearing_label(b) == "E"


def test_bearing_label_wrap():
    assert bearing_label(350) == "N"
    assert bearing_label(10) == "N"
    assert bearing_label(45) == "NE"
    assert bearing_label(135) == "SE"
    assert bearing_label(225) == "SW"
    assert bearing_label(315) == "NW"


def test_priority_scoring():
    from strands_guardian.tools.dossier_tools import _score_priority, Priority

    # No threats = P3
    p, s = _score_priority(0, 0, 0, 0)
    assert p == Priority.P3

    # Ransomware KEV = always P1
    p, s = _score_priority(0, 0, 0, 0, has_kev_ransomware=True)
    assert p == Priority.P1

    # High threat count + KEV + severe geo
    p, s = _score_priority(3, 1, 2, 2)
    assert p in (Priority.P1, Priority.P2)
