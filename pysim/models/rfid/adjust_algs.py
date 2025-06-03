# --- Query Adjust Strategies ---
import math

from enum import Enum

class QueryAdjustStrategy(Enum):
    SYMMETRIC = "symmetric"
    DYNAMIC = "dynamic"

def symmetric_query_adjust(q_fp, q, delta):
    return min(15, q_fp + delta)

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
    QueryAdjustStrategy.SYMMETRIC: symmetric_query_adjust,
    QueryAdjustStrategy.DYNAMIC: dynamic_query_adjust,
}
