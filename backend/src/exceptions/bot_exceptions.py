class BotError(Exception):
    """Basisklasse für alle fachlichen Fehler rund um Bots."""


class BotNotFoundError(BotError):
    """Wird geworfen, wenn ein Bot nicht in der Datenbank existiert."""

    def __init__(self, symbol: str, message: str | None = None):
        self.symbol = symbol
        super().__init__(message or f"Bot with symbol '{symbol}' does not exist.")

class BotRunningError(BotError):
    """Wird geworfen, wenn eine Aktion wegen eines laufenden Bots blockiert ist."""

    def __init__(self, symbol: str, message: str | None = None):
        self.symbol = symbol
        super().__init__(message or f"Bot with symbol '{symbol}' is currently running.")


class BotAlreadyExistsError(BotError):
    """Wird geworfen, wenn bereits ein Bot mit diesem Symbol existiert."""

    def __init__(self, symbol: str, message: str | None = None):
        self.symbol = symbol
        super().__init__(message or f"Bot with symbol '{symbol}' already exists.")