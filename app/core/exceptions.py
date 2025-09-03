from typing import Optional, Dict, Any


class LexiException(Exception):
    """Base exception for Lexi application"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class JagritiServiceException(LexiException):
    """Exceptions related to Jagriti service operations"""
    pass


class ValidationException(LexiException):
    """Input validation exceptions"""
    pass


class StateNotFoundException(JagritiServiceException):
    """State not found in mappings"""
    pass


class CommissionNotFoundException(JagritiServiceException):
    """Commission not found for given state"""
    pass


class SearchTimeoutException(JagritiServiceException):
    """Search operation timed out"""
    pass


class CaptchaRequiredException(JagritiServiceException):
    """Captcha verification required"""
    pass


class RateLimitExceededException(LexiException):
    """Rate limit exceeded"""
    pass


class SessionExpiredException(JagritiServiceException):
    """Session has expired, re-authentication needed"""
    pass