from pydantic import BaseModel, Field


class Result(BaseModel):
    avg_interval: float = Field(..., description="Average ping interval")
    avg_delay: float = Field(..., description="Average transmission delay")
    miss_rate: float = Field(..., description="Probability of missing Pong")
