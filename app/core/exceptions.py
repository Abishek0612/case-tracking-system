from typing import Optional, Dict, Any


class LexiException(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class JagritiServiceException(LexiException):
    pass


class StateNotFoundException(JagritiServiceException):
    pass


class CommissionNotFoundException(JagritiServiceException):
    pass


class SearchTimeoutException(JagritiServiceException):
    pass