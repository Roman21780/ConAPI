class WBError(Exception):
    """Базовое исключение для ошибок API Wildberries"""
    pass

class WBAuthError(WBError):
    """Ошибка авторизации"""
    pass

class WBValidationError(WBError):
    """Ошибка валидации данных"""
    pass

class WBAPIError(WBError):
    """Ошибка при вызове API"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code