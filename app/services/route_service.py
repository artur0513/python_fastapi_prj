import math
from collections import defaultdict
from typing import Dict, List, Optional
from sqlmodel import Session

from app.models.models import Order, User, PickupPoint, OrderStatusEnum


def haversine(lat1, lon1, lat2, lon2):
    """Вычисляет расстояние в метрах между двумя точками (геодезическая формула)."""
    r = 6371000  # радиус Земли в метрах
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_route(session: Session, courier_id: int) -> Dict:
    """
    Строит оптимальный маршрут для курьера без изменения статусов заказов.
    Заказы NEW: нужен pickup из соответствующей точки выдачи.
    Заказы IN_DELIVERY: нужна только доставка.
    """
    courier = session.get(User, courier_id)
    if not courier:
        raise ValueError("Курьер не найден")
    if courier.latitude is None or courier.longitude is None:
        raise ValueError("Курьер не указал свои координаты")

    orders = (
        session.query(Order)
        .filter(
            Order.assigned_courier_id == courier_id,
            Order.status != OrderStatusEnum.DELIVERED,
        )
        .all()
    )

    if not orders:
        return {"route": [], "total_distance_meters": 0.0}

    # Проверка существования точек выдачи у новых заказов
    for order in orders:
        if order.status == OrderStatusEnum.NEW:
            if not order.pickup_point:
                raise ValueError(f"У заказа {order.id} отсутствует точка выдачи")
            if order.pickup_point.latitude is None or order.pickup_point.longitude is None:
                raise ValueError(f"Точка выдачи у заказа {order.id} не имеет координат")

    # Группировка заказов
    new_by_pickup: Dict[int, List[Order]] = defaultdict(list)
    pending_deliveries: List[Order] = []

    for order in orders:
        if order.status == OrderStatusEnum.NEW:
            new_by_pickup[order.pickup_point_id].append(order)
        elif order.status == OrderStatusEnum.IN_DELIVERY:
            pending_deliveries.append(order)

    # Алгоритм Cheapest Insertion + 2-opt

    # Вспомогательный класс
    class RoutePoint:
        """Одна точка маршрута: старт, pickup или delivery."""
        def __init__(
            self,
            r_point_type: str,      # "start", "pickup", "delivery"
            lat: float,
            lon: float,
            order_ids: Optional[List[int]] = None,
            pickup_point_id: Optional[int] = None,
            order_id: Optional[int] = None,
            description: Optional[str] = None,
        ):
            self.type = r_point_type
            self.lat = lat
            self.lon = lon
            self.order_ids = order_ids or []      # для pickup – id всех заказов
            self.pickup_point_id = pickup_point_id
            self.order_id = order_id              # для delivery – конкретный заказ
            self.description = description

    # Стартовая точка – текущее положение курьера
    start_route_point = RoutePoint("start", courier.latitude, courier.longitude)
    route = [start_route_point]          # маршрут всегда начинается с курьера

    # Собираем все события, которые нужно вставить
    uninserted_pickups = {}       # pickup_point_id > RoutePoint (с указанием заказов)
    uninserted_deliveries = []    # список RoutePoint для доставок (NEW и IN_DELIVERY)

    # Pickup-точки для групп заказов NEW
    for pickup_id, group_orders in new_by_pickup.items():
        point = session.get(PickupPoint, pickup_id)  # уже проверено, что существует
        r_point = RoutePoint(
            "pickup",
            point.latitude,
            point.longitude,
            order_ids=[o.id for o in group_orders],
            pickup_point_id=pickup_id,
        )
        uninserted_pickups[pickup_id] = r_point

    # Доставки для заказов NEW
    for pickup_id, group_orders in new_by_pickup.items():
        for order in group_orders:
            r_point = RoutePoint(
                "delivery",
                order.delivery_latitude,
                order.delivery_longitude,
                order_id=order.id,
                description=order.description,
                pickup_point_id=pickup_id,  # нужно для проверки порядка
            )
            uninserted_deliveries.append(r_point)

    # Доставки для заказов IN_DELIVERY (без pickup)
    for order in pending_deliveries:
        r_point = RoutePoint(
            "delivery",
            order.delivery_latitude,
            order.delivery_longitude,
            order_id=order.id,
            description=order.description,
            # pickup_point_id отсутствует, т.е. не требует предварительного забора
        )
        uninserted_deliveries.append(r_point)

    # Единый список не вставленных точек
    uninserted_events: List[RoutePoint] = list(uninserted_pickups.values()) + uninserted_deliveries

    # Расчёта стоимости вставки
    def insertion_cost(r: List[RoutePoint], pos: int, event: RoutePoint) -> float:
        """На сколько увеличится длина маршрута при вставке event на позицию pos (1..len(r))."""
        prev = r[pos-1]
        if pos < len(r):
            nxt = r[pos]
            old_edge = haversine(prev.lat, prev.lon, nxt.lat, nxt.lon)
            new_edges = haversine(prev.lat, prev.lon, event.lat, event.lon) + haversine(event.lat, event.lon, nxt.lat, nxt.lon)
            return new_edges - old_edge
        else:
            # вставка в конец
            return haversine(prev.lat, prev.lon, event.lat, event.lon)

    # Построение начального приближения маршрута методом cheapest insertion
    while uninserted_events:
        best_cost = float("inf")
        best_event = None
        best_pos = -1

        for event in uninserted_events:
            # Определяем допустимые позиции вставки
            if event.type == "pickup":
                allowed_positions = range(1, len(route) + 1)  # любое место после start
            else:  # delivery
                # Если у доставки есть pickup, она может быть вставлена только после него
                if event.pickup_point_id is not None:
                    # Находим индекс уже вставленного pickup в маршруте
                    pickup_idx = None
                    for idx, s in enumerate(route):
                        if s.type == "pickup" and s.pickup_point_id == event.pickup_point_id:
                            pickup_idx = idx
                            break
                    if pickup_idx is None:
                        # Pickup ещё не вставлен – пропускаем
                        continue
                    allowed_positions = range(pickup_idx + 1, len(route) + 1)
                else:
                    # standalone delivery – можно вставлять куда угодно после start
                    allowed_positions = range(1, len(route) + 1)

            # Перебираем допустимые позиции
            for pos in allowed_positions:
                cost = insertion_cost(route, pos, event)
                if cost < best_cost:
                    best_cost = cost
                    best_event = event
                    best_pos = pos

        # Вставляем лучшее событие
        route.insert(best_pos, best_event)
        uninserted_events.remove(best_event)

    # Функция проверки порядка pickup–delivery
    def is_order_valid(r: List[RoutePoint]) -> bool:
        """Проверяет, что для каждого заказа pickup находится перед delivery."""
        # Соберём для каждого order_id индекс его появления
        # Для заказов с pickup: индекс pickup и индекс delivery
        pickup_idx = {}
        delivery_idx = {}
        for i, r_point in enumerate(r):
            if r_point.type == "pickup":
                for oid in r_point.order_ids:
                    pickup_idx[oid] = i
            elif r_point.type == "delivery" and r_point.order_id is not None:
                delivery_idx[r_point.order_id] = i
        # Проверяем все заказы, имеющие pickup
        for oid, p_idx in pickup_idx.items():
            d_idx = delivery_idx.get(oid)
            if d_idx is not None and d_idx <= p_idx:
                return False
        return True

    # 2-opt - улучшение начального алгоритма
    improved = True
    while improved:
        improved = False
        n = len(route)
        # Перебираем пары рёбер (a, b) и (c, d)
        for a in range(1, n - 2):       # a = i-1, не трогаем start (index 0)
            b = a + 1
            for d in range(a + 2, n):   # d = j
                c = d - 1
                # Текущие рёбра: (route[a], route[b]) и (route[c], route[d])
                old_dist = haversine(route[a].lat, route[a].lon, route[b].lat, route[b].lon) \
                         + haversine(route[c].lat, route[c].lon, route[d].lat, route[d].lon)
                # Новые рёбра: (route[a], route[c]) и (route[b], route[d]) при развороте сегмента b..c
                new_dist = haversine(route[a].lat, route[a].lon, route[c].lat, route[c].lon) \
                         + haversine(route[b].lat, route[b].lon, route[d].lat, route[d].lon)

                if new_dist < old_dist - 1e-6:   # значимое улучшение
                    # Строим кандидата: разворачиваем сегмент [b..c]
                    candidate = route[:b] + list(reversed(route[b:c+1])) + route[c+1:]
                    if is_order_valid(candidate):
                        route = candidate
                        improved = True
                        break
            if improved:
                break

    # Формирование результата
    route_steps = []
    total_dist = 0.0
    prev = route[0]
    for r_point in route[1:]:   # стартовую точку пропускаем
        total_dist += haversine(prev.lat, prev.lon, r_point.lat, r_point.lon)
        prev = r_point
        if r_point.type == "pickup":
            route_steps.append({
                "type": "pickup",
                "pickup_point_id": r_point.pickup_point_id,
                "orders": r_point.order_ids,
                "latitude": r_point.lat,
                "longitude": r_point.lon,
            })
        elif r_point.type == "delivery":
            route_steps.append({
                "type": "delivery",
                "order_id": r_point.order_id,
                "description": r_point.description,
                "latitude": r_point.lat,
                "longitude": r_point.lon,
            })

    return {
        "route": route_steps,
        "total_distance_meters": round(total_dist, 2),
        "start_point": {
            "latitude": courier.latitude,
            "longitude": courier.longitude,
        },
    }

