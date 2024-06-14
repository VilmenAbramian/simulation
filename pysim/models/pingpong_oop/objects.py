from pydantic import BaseModel, Field


class Config(BaseModel):
    interval: float
    channel_delay: float
    service_delay: float
    loss_prob: float
    max_pings: int | None = None


class Result(BaseModel):
    avg_interval: float = Field(..., description="Average ping interval")
    avg_delay: float = Field(..., description="Average transmission delay")
    miss_rate: float = Field(..., description="Probability of missing Pong")
