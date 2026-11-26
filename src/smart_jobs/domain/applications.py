APPLICATION_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"awaiting_approval"}),
    "awaiting_approval": frozenset({"approved"}),
    "approved": frozenset({"awaiting_approval", "sent"}),
    "sent": frozenset({"test", "interview", "rejected", "withdrawn"}),
    "test": frozenset({"interview", "rejected", "withdrawn"}),
    "interview": frozenset({"offer", "rejected", "withdrawn"}),
    "offer": frozenset({"accepted", "declined"}),
    "rejected": frozenset(),
    "withdrawn": frozenset(),
    "accepted": frozenset(),
    "declined": frozenset(),
}


class InvalidApplicationTransition(ValueError):
    pass


def validate_application_transition(
    current: str,
    target: str,
    *,
    manual_submission_confirmed: bool,
) -> None:
    if target not in APPLICATION_TRANSITIONS.get(current, frozenset()):
        raise InvalidApplicationTransition(f"Transicao invalida: {current} -> {target}")
    if target == "sent" and not manual_submission_confirmed:
        raise InvalidApplicationTransition(
            "Envio so pode ser registrado com confirmacao humana explicita"
        )
