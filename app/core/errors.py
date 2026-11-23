class AppError(Exception):
    """Base class for errors that map directly to an HTTP response."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, 404)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, 409)


class LLMError(AppError):
    """The AI model is unreachable, timed out, or returned unusable output."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message, status_code)
