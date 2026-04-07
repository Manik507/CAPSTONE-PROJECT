class ApiError(Exception):
    def __init__(self, message, status_code=400, error_code=None, **kwargs):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        # Support both 'error' and 'error_code' for flexibility
        self.error_code = kwargs.get('error') or error_code or "api_error"
        self.details = kwargs.get('details')

    def to_dict(self):
        rv = {"message": self.message, "error": self.error_code}
        if self.details:
            rv["details"] = self.details
        return rv
