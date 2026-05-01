def test_get_me(client, courier_token):
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {courier_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "courier"


def test_update_coords(client, courier_token):
    resp = client.put(
        "/users/me/coords",
        json={"latitude": 55.75, "longitude": 37.61},
        headers={"Authorization": f"Bearer {courier_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["latitude"] == 55.75
    assert data["longitude"] == 37.61
