import requests

BASE = "http://127.0.0.1:8000"

# Регистрация
mgr = requests.post(f"{BASE}/auth/signup", json={
    "email": "manager@d.ru", "password": "1234", "full_name": "Kaban Kabanich", "role": "manager"
}).json()
print("Manager:", mgr)
token_mgr = requests.post(f"{BASE}/auth/login", data={"username": "manager@d.ru", "password": "1234"}).json()[
    "access_token"]
print(f"Token Manager: {token_mgr}")

cr = requests.post(f"{BASE}/auth/signup", json={
    "email": "courier@d.ru", "password": "1234", "full_name": "Courier Mojave Express", "role": "courier"
}).json()
print("Courier:", cr)
token_cr = requests.post(f"{BASE}/auth/login", data={"username": "courier@d.ru", "password": "1234"}).json()[
    "access_token"]
print(f"Token Courier: {token_mgr}")


head_m = {"Authorization": f"Bearer {token_mgr}"}
head_c = {"Authorization": f"Bearer {token_cr}"}

# Точки выдачи
points = [
    {"name": "Склад 1", "address": "Красная пл., 1", "latitude": 55.75393, "longitude": 37.62080},
    {"name": "Склад 2", "address": "Ленинский пр-т, 30", "latitude": 55.715, "longitude": 37.615},
    {"name": "Склад 3", "address": "Дмитровское ш., 20", "latitude": 55.785, "longitude": 37.615}
]
pids = []
for p in points:
    r = requests.post(f"{BASE}/pickup-points", json=p, headers=head_m)
    pids.append(r.json()["id"])
    print("Point:", r.json())

# Заказы
orders_data = [
    {"description": "Книги", "weight": 3.5, "delivery_latitude": 55.76, "delivery_longitude": 37.62,
     "pickup_point_id": pids[0], "assigned_courier_id": cr["id"]},
    {"description": "Ноутбук", "weight": 1.2, "delivery_latitude": 55.77, "delivery_longitude": 37.63,
     "pickup_point_id": pids[0], "assigned_courier_id": cr["id"]},
    {"description": "Продукты", "weight": 5.0, "delivery_latitude": 55.72, "delivery_longitude": 37.61,
     "pickup_point_id": pids[1], "assigned_courier_id": cr["id"]},
    {"description": "Цветы (уже в пути)", "weight": 0.8, "delivery_latitude": 55.78, "delivery_longitude": 37.625,
     "pickup_point_id": pids[1], "assigned_courier_id": cr["id"]}
]
oid = []
for o in orders_data:
    r = requests.post(f"{BASE}/orders", json=o, headers=head_m)
    oid.append(r.json()["id"])
    print("Order:", r.json())

# Установим координаты курьера
requests.put(f"{BASE}/users/me/coords", json={"latitude": 55.751244, "longitude": 37.618423}, headers=head_c)
print("Coords updated")

# Заберём последний заказ
requests.post(f"{BASE}/courier/pickup-order/{oid[-1]}", headers=head_c)
print("Order", oid[-1], "picked up")
