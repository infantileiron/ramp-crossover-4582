from dataclasses import asdict, dataclass
from decimal import Decimal

from src.constants.domain import Sequence


@dataclass(frozen=True)
class Pair:
    code: str
    sequence: Sequence
    period1: Decimal | None
    period2: Decimal | None

    def snapshot(self):
        return {key: format(value, '.2f') if isinstance(value, Decimal) else value for key, value in asdict(self).items()}
