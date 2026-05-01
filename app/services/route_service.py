import math
from sqlmodel import Session

from app.models.models import Order, User, OrderStatusEnum


def haversine(lat1, lon1, lat2, lon2):
    """Вычисляет расстояние в метрах между двумя точками (геодезическая формула)."""
    r = 6371000  # радиус Земли в метрах
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_route(session: Session, courier_id: int) -> dict:
    """
    Строит оптимальный маршрут (жадный алгоритм) для курьера.
    Переводит заказы new → in_delivery.
    Возвращает словарь с маршрутом и расстоянием.
    """
    courier = session.get(User, courier_id)
    if not courier:
        raise ValueError("Курьер не найден")
    if courier.latitude is None or courier.longitude is None:
        raise ValueError("Курьер не указал свои координаты")

    # Получаем заказы, назначенные курьеру, не доставленные
    orders = session.query(Order).filter(
        Order.assigned_courier_id == courier_id,
        Order.status != OrderStatusEnum.DELIVERED
    ).all()

    if not orders:
        return {"route": [], "total_distance": 0.0}

    # Переводим все "new" в "in_delivery"
    for order in orders:
        if order.status == OrderStatusEnum.NEW:
            order.status = OrderStatusEnum.IN_DELIVERY
            session.add(order)
    session.commit()

    # Жадный алгоритм
    current_lat = courier.latitude
    current_lon = courier.longitude
    remaining = orders.copy()
    route = []
    total_dist = 0.0

    while remaining:
        # Находим ближайший заказ
        distances = []
        for order in remaining:
            d = haversine(current_lat, current_lon, order.delivery_latitude,
                          order.delivery_longitude)
            distances.append((d, order))
        distances.sort(key=lambda x: x[0])
        nearest_dist, nearest_order = distances[0]

        route.append(nearest_order)
        total_dist += nearest_dist
        current_lat = nearest_order.delivery_latitude
        current_lon = nearest_order.delivery_longitude
        remaining.remove(nearest_order)

    # Формируем ответ: список словарей с id, координатами, адресом (опционально)
    route_data = [
        {
            "order_id": o.id,
            "description": o.description,
            "delivery_latitude": o.delivery_latitude,
            "delivery_longitude": o.delivery_longitude,
            "status": o.status,
        }
        for o in route
    ]

    return {
        "route": route_data,
        "total_distance_meters": round(total_dist, 2),
        "start_point": {
            "latitude": courier.latitude,
            "longitude": courier.longitude
        }
    }
