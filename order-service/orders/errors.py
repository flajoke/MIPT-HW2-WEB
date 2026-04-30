class AppError(Exception):
    def __init__(self, status: int, message: str, details: dict | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details or None


class ValidationError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(400, message, details)


class NotFoundError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(404, message, details)


class ConflictError(AppError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(409, message, details)


class UpstreamError(AppError):
    pass
