class ApiError(Exception):
    def __init__(self, message, status_code=400, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

    def to_dict(self):
        rv = {"message": self.message, "error": self.error_code or "api_error"}
        return rv
