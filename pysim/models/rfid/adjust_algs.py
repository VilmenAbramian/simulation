# --- Query Adjust Strategies ---
import math

from enum import Enum

class QueryAdjustStrategy(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"

def static_query_adjust(q_fp, direction, q):
    if q == 0:
        q = 0.8
    delta = 0.3
    if direction < 0:
        return max(0, q_fp - delta)
    elif direction > 0:
        return min(15, q_fp + delta)
    else:
        return q_fp

def dynamic_query_adjust(q_fp, q, delta):
    """
    Δ изменяется по направлению и зависит от Q:
    - При Q ≈ 0 → Δ ≈ 0.5
    - При Q ≈ 15 → Δ ≈ 0.2
    - delta по знаку зависит от ситуации (коллизия или одиночный ответ)
    """
    magnitude = max(0.1, 0.5 / (1 + 0.04 * q))  # более плавное снижение
    return min(15, max(0, q_fp + math.copysign(magnitude, delta)))

QUERY_ADJUST_FUNCTIONS = {
    QueryAdjustStrategy.STATIC: static_query_adjust,
    QueryAdjustStrategy.DYNAMIC: dynamic_query_adjust,
}
