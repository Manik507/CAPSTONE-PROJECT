class ApiError(Exception):
    """Typed exception for returning clean JSON errors."""

    def __init__(self, message, status_code=400, error="bad_request", details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error
        self.details = details or {}

    def to_dict(self):
        payload = {"error": self.error, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload

