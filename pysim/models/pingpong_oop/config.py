from pydantic import BaseModel, Field


class Config(BaseModel):
    interval: float
    channel_delay: float
    service_delay: float
    loss_prob: float
    max_pings: int | None = None
