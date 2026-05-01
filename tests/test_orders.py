import pytest


def sample_pickup_point_id(client, manager_token):
    resp = client.post(
        "/pickup-points",
        json={"name": "ПВЗ", "address": "Москва", "latitude": 55.0, "longitude": 37.0},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    return resp.json()["id"]


def sample_courier_id(client):
    import random
    email = f"courier{random.randint(1000, 9999)}@test.com"
    resp = client.post("/auth/signup", json={
        "email": email,
        "password": "pass",
        "full_name": "Courier",
        "role": "courier"
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_order(client, manager_token, sample_pickup_point_id, sample_courier_id):
    order_data = {
        "description": "Доставить пиццу",
        "weight": 2.5,
        "delivery_latitude": 55.1,
        "delivery_longitude": 37.2,
        "pickup_point_id": sample_pickup_point_id,
        "assigned_courier_id": sample_courier_id
    }
    resp = client.post("/orders", json=order_data, headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "new"


def test_list_orders_with_filter(client, manager_token, sample_pickup_point_id, sample_courier_id):
    order1 = {"description": "Заказ 1", "delivery_latitude": 55.0, "delivery_longitude": 37.0,
              "pickup_point_id": sample_pickup_point_id, "assigned_courier_id": sample_courier_id}
    order2 = {"description": "Заказ 2", "delivery_latitude": 55.1, "delivery_longitude": 37.1,
              "pickup_point_id": sample_pickup_point_id, "assigned_courier_id": sample_courier_id}
    client.post("/orders", json=order1, headers={"Authorization": f"Bearer {manager_token}"})
    client.post("/orders", json=order2, headers={"Authorization": f"Bearer {manager_token}"})
    resp = client.get("/orders?status=new", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    resp = client.get(f"/orders?courier_id={sample_courier_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert len(resp.json()) == 2
    resp = client.get("/orders?courier_id=9999", headers={"Authorization": f"Bearer {manager_token}"})
    assert len(resp.json()) == 0
