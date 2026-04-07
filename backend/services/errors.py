class ApiError(Exception):
    def __init__(self, message, status_code=400, error="api_error", details=None, **kwargs):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = kwargs.get('error') or kwargs.get('error_code') or error
        self.details = details or kwargs.get('details') or {}

    def to_dict(self):
        payload = {
            "error": self.error,
            "message": self.message
        }
        if self.details:
            payload["details"] = self.details
        return payload