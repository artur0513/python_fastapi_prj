def test_pickup_order(client, courier_token, manager_token):
    # Подготовка
    pick_resp = client.post("/pickup-points",
        json={"name": "ПВ", "address": "Москва", "latitude": 55.0, "longitude": 37.0},
        headers={"Authorization": f"Bearer {manager_token}"})
    point_id = pick_resp.json()["id"]
    me_resp = client.get("/users/me", headers={"Authorization": f"Bearer {courier_token}"})
    courier_id = me_resp.json()["id"]
    order_data = {
        "description": "Заказ",
        "delivery_latitude": 55.8,
        "delivery_longitude": 37.7,
        "pickup_point_id": point_id,
        "assigned_courier_id": courier_id
    }
    ord_resp = client.post("/orders", json=order_data, headers={"Authorization": f"Bearer {manager_token}"})
    order_id = ord_resp.json()["id"]

    # Пробуем забрать чужой заказ (должен быть 403)
    # Создаём другого курьера
    import random
    other_email = f"other{random.randint(1000,9999)}@test.com"
    client.post("/auth/signup", json={"email": other_email, "password": "pass", "full_name": "Other", "role": "courier"})
    other_login = client.post("/auth/login", data={"username": other_email, "password": "pass"})
    other_token = other_login.json()["access_token"]
    resp = client.post(f"/courier/pickup-order/{order_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403

    # Забираем свой
    resp = client.post(f"/courier/pickup-order/{order_id}", headers={"Authorization": f"Bearer {courier_token}"})
    assert resp.status_code == 200
    # Проверяем статус
    get_resp = client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert get_resp.json()["status"] == "in_delivery"


def test_courier_route(client, courier_token, manager_token):
    # Создаём две точки и два заказа: один оставим new, другой переведём в in_delivery
    # точка 1
    p1 = client.post("/pickup-points",
        json={"name": "ПВ1", "address": "Москва1", "latitude": 55.0, "longitude": 37.0},
        headers={"Authorization": f"Bearer {manager_token}"}).json()
    p2 = client.post("/pickup-points",
        json={"name": "ПВ2", "address": "Москва2", "latitude": 55.1, "longitude": 37.1},
        headers={"Authorization": f"Bearer {manager_token}"}).json()
    me = client.get("/users/me", headers={"Authorization": f"Bearer {courier_token}"}).json()
    courier_id = me["id"]

    # Обновим координаты курьера
    client.put("/users/me/coords", json={"latitude": 55.75, "longitude": 37.61},
               headers={"Authorization": f"Bearer {courier_token}"})

    # Заказ 1 (будет new)
    o1 = client.post("/orders", json={
        "description": "З1",
        "delivery_latitude": 55.8,
        "delivery_longitude": 37.7,
        "pickup_point_id": p1["id"],
        "assigned_courier_id": courier_id
    }, headers={"Authorization": f"Bearer {manager_token}"}).json()
    # Заказ 2 (переведём в in_delivery)
    o2 = client.post("/orders", json={
        "description": "З2",
        "delivery_latitude": 55.9,
        "delivery_longitude": 37.8,
        "pickup_point_id": p2["id"],
        "assigned_courier_id": courier_id
    }, headers={"Authorization": f"Bearer {manager_token}"}).json()

    # Забираем второй заказ
    client.post(f"/courier/pickup-order/{o2['id']}", headers={"Authorization": f"Bearer {courier_token}"})

    # Запрашиваем маршрут
    route_resp = client.get("/courier/route", headers={"Authorization": f"Bearer {courier_token}"})
    assert route_resp.status_code == 200
    data = route_resp.json()
    assert len(data["route"]) >= 2  # минимум два шага: pickup З1 и доставка З2 (в каком-то порядке)
    # Проверим, что статусы не изменились в БД
    check_o1 = client.get(f"/orders/{o1['id']}", headers={"Authorization": f"Bearer {manager_token}"}).json()
    assert check_o1["status"] == "new"
    check_o2 = client.get(f"/orders/{o2['id']}", headers={"Authorization": f"Bearer {manager_token}"}).json()
    assert check_o2["status"] == "in_delivery"
