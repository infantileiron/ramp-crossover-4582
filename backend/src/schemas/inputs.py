from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from src.constants.domain import Decision, Sequence

RouteCode = Annotated[str, StringConstraints(pattern=r'^R[0-9]{2}$')]
PairCode = Annotated[str, StringConstraints(pattern=r'^[A-Z0-9][A-Z0-9-]{1,19}$')]
SlotCode = PairCode
Seat = Literal[1, 2]
Seconds = Annotated[Decimal, Field(gt=0, le=900, decimal_places=2)]


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Credentials(Input):
    username: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)


class PairInput(Input):
    sequence: Sequence
    period1: Seconds | None
    period2: Seconds | None

    @model_validator(mode='after')
    def has_observation(self):
        if self.period1 is None and self.period2 is None:
            raise ValueError('至少录入一个周期的用时')
        return self


class PlanInput(Input):
    route_code: RouteCode
    edition: str = Field(min_length=1, max_length=40)
    min_pairs: int = Field(ge=2, le=50)
    gap_limit: Annotated[Decimal, Field(gt=0, le=120, decimal_places=2)]


class RunInput(Input):
    plan_id: int = Field(gt=0, le=2147483647)


class ReviewInput(Input):
    decision: Decision
    note: str = Field(min_length=4, max_length=500)


class SessionCreate(Input):
    slot_code: SlotCode
    starts_at: datetime
    seat1_code: PairCode
    seat2_code: PairCode


class SessionSwap(Input):
    participant_code: PairCode


class SessionStart(Input):
    seat: Seat
    participant_code: PairCode


class SessionTimes(Input):
    period1: Seconds | None
    period2: Seconds | None

    @model_validator(mode='after')
    def has_observation(self):
        if self.period1 is None and self.period2 is None:
            raise ValueError('至少录入一个周期的用时')
        return self
