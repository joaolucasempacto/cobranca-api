class AppError(Exception):
    """Exceção base para todos os erros de domínio da aplicação."""

    def __init__(self, message: str = "Ocorreu um erro inesperado") -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    """Recurso não encontrado."""

    def __init__(self, message: str = "Recurso não encontrado") -> None:
        super().__init__(message)


class ConflictError(AppError):
    """Conflito de estado (ex: recurso duplicado)."""

    def __init__(self, message: str = "Conflito de dados") -> None:
        super().__init__(message)


class UnauthorizedError(AppError):
    """Usuário não autenticado."""

    def __init__(self, message: str = "Não autorizado") -> None:
        super().__init__(message)


class ForbiddenError(AppError):
    """Usuário autenticado, mas sem permissão (RBAC)."""

    def __init__(self, message: str = "Acesso negado") -> None:
        super().__init__(message)
