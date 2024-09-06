from pydantic import BaseModel


class Config(BaseModel):
    probability: tuple
    processing_time: tuple
    max_transmisions: int | None = None
    chunks_number: int
    scenario: int
