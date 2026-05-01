def test_create_pickup_point_as_manager(client, manager_token):
    resp = client.post(
        "/pickup-points",
        json={"name": "Склад", "address": "ул. Ленина, 1", "latitude": 55.0, "longitude": 37.0},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert resp.status_code == 201


def test_create_pickup_point_as_courier_forbidden(client, courier_token):
    resp = client.post(
        "/pickup-points",
        json={"name": "Склад", "address": "ул. Ленина, 1", "latitude": 55.0, "longitude": 37.0},
        headers={"Authorization": f"Bearer {courier_token}"}
    )
    assert resp.status_code == 403


def test_list_pickup_points(client, manager_token):
    client.post("/pickup-points", json={"name": "Точка 1", "address": "1", "latitude": 1.0, "longitude": 1.0},
                headers={"Authorization": f"Bearer {manager_token}"})
    resp = client.get("/pickup-points", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
