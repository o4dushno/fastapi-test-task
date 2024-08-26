class SocketException(BaseException):
    # Ошибка сокетов
    ...


class SocketPermissionError(SocketException):
    ...


class SocketUserNotFoundError(SocketException):
    ...
