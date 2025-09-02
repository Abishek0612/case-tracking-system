class JagritiServiceException(Exception):
    pass


class ValidationException(Exception):
    pass


class StateNotFoundException(JagritiServiceException):
    pass


class CommissionNotFoundException(JagritiServiceException):
    pass