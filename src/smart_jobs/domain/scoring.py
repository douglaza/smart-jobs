from dataclasses import dataclass


@dataclass(frozen=True)
class Rubric:
    version: str
    required_weight: int
    desirable_weight: int
    experience_weight: int

    def validate(self) -> None:
        if (
            sum(
                (
                    self.required_weight,
                    self.desirable_weight,
                    self.experience_weight,
                )
            )
            != 100
        ):
            raise ValueError("Pesos da rubrica devem somar 100")


CONFIRMED_RUBRIC = Rubric(
    version="phase3-2026-11",
    required_weight=50,
    desirable_weight=30,
    experience_weight=20,
)
