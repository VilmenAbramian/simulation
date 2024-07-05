from pydantic import BaseModel, Field


class Config(BaseModel):
    probability: tuple
    processing_time: tuple
    max_transmisions: int | None = None


class Result(BaseModel):
    avg_time: float = Field(..., description='Среднее время до поглощения')
