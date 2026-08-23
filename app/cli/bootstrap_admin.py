import argparse

from pydantic import ValidationError

from app.database.session import SessionLocal
from app.exceptions.base import AppError
from app.repositories.unit_of_work import UnitOfWork
from app.schemas.user import UserCreate
from app.services.bootstrap_service import BootstrapService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cria ou completa o administrador inicial do sistema."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        payload = UserCreate(email=args.email, password=args.password)
        with SessionLocal() as session:
            with UnitOfWork(session) as uow:
                user = BootstrapService(uow).bootstrap_admin(
                    email=str(payload.email),
                    password=payload.password,
                )
    except (AppError, ValidationError) as exc:
        print(f"Bootstrap não concluído: {exc}")
        return 1

    print(f"Administrador pronto: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
