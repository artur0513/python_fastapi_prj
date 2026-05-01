def test_courier_route(client, courier_token, manager_token):
    # Создаём точку выдачи через менеджера
    point_resp = client.post("/pickup-points",
                             json={"name": "ПВ", "address": "Москва", "latitude": 55.0, "longitude": 37.0},
                             headers={"Authorization": f"Bearer {manager_token}"})
    point_id = point_resp.json()["id"]

    # Получаем ID курьера, который залогинен с courier_token
    me_resp = client.get("/users/me", headers={"Authorization": f"Bearer {courier_token}"})
    courier_id = me_resp.json()["id"]

    # Обновляем координаты курьера
    client.put("/users/me/coords", json={"latitude": 55.75, "longitude": 37.61},
               headers={"Authorization": f"Bearer {courier_token}"})

    # Менеджер создаёт заказ для этого курьера
    order = {
        "description": "Тестовый",
        "delivery_latitude": 55.8,
        "delivery_longitude": 37.7,
        "pickup_point_id": point_id,
        "assigned_courier_id": courier_id
    }
    client.post("/orders", json=order, headers={"Authorization": f"Bearer {manager_token}"})

    # Запрос маршрута
    route_resp = client.get("/courier/route", headers={"Authorization": f"Bearer {courier_token}"})
    assert route_resp.status_code == 200
    data = route_resp.json()
    assert len(data["route"]) == 1
    assert data["route"][0]["status"] == "in_delivery"


def test_complete_order(client, courier_token, manager_token):
    # Аналогичная подготовка
    point_resp = client.post("/pickup-points",
                             json={"name": "ПВ", "address": "Москва", "latitude": 55.0, "longitude": 37.0},
                             headers={"Authorization": f"Bearer {manager_token}"})
    point_id = point_resp.json()["id"]
    me_resp = client.get("/users/me", headers={"Authorization": f"Bearer {courier_token}"})
    courier_id = me_resp.json()["id"]
    client.put("/users/me/coords", json={"latitude": 55.75, "longitude": 37.61},
               headers={"Authorization": f"Bearer {courier_token}"})
    order = {
        "description": "Тест",
        "delivery_latitude": 55.8,
        "delivery_longitude": 37.7,
        "pickup_point_id": point_id,
        "assigned_courier_id": courier_id
    }
    ord_resp = client.post("/orders", json=order, headers={"Authorization": f"Bearer {manager_token}"})
    order_id = ord_resp.json()["id"]

    # Сначала маршрут (чтобы заказ перешёл в in_delivery)
    client.get("/courier/route", headers={"Authorization": f"Bearer {courier_token}"})
    # Завершаем заказ
    complete_resp = client.post(f"/courier/complete-order/{order_id}",
                                headers={"Authorization": f"Bearer {courier_token}"})
    assert complete_resp.status_code == 200
    # Проверяем статус
    get_resp = client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert get_resp.json()["status"] == "delivered"
