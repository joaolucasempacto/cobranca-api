import ast
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def python_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.py"))


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)

    return modules


def commit_calls(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "commit"
    ]


class ArchitectureBoundaryTests(TestCase):
    def test_services_do_not_depend_on_fastapi(self) -> None:
        violations: list[str] = []

        for path in python_files(APP / "services"):
            modules = imported_modules(path)
            if any(module.startswith("fastapi") for module in modules):
                violations.append(path.name)

        self.assertEqual(
            violations,
            [],
            f"Services must not depend on FastAPI: {violations}",
        )

    def test_routers_do_not_access_database_or_repositories(self) -> None:
        violations: list[str] = []

        for path in python_files(APP / "routers"):
            modules = imported_modules(path)
            forbidden = sorted(
                module
                for module in modules
                if module.startswith(("app.database", "app.repositories"))
            )
            if forbidden:
                violations.append(f"{path.name}: {', '.join(forbidden)}")

        self.assertEqual(
            violations,
            [],
            f"Routers must not access persistence directly: {violations}",
        )

    def test_models_do_not_depend_on_upper_layers(self) -> None:
        violations: list[str] = []

        for path in python_files(APP / "models"):
            modules = imported_modules(path)
            forbidden = sorted(
                module
                for module in modules
                if module.startswith(
                    (
                        "fastapi",
                        "app.repositories",
                        "app.services",
                        "app.routers",
                    )
                )
            )
            if forbidden:
                violations.append(f"{path.name}: {', '.join(forbidden)}")

        self.assertEqual(
            violations,
            [],
            f"Models must remain framework and upper-layer agnostic: {violations}",
        )

    def test_application_does_not_use_create_all(self) -> None:
        violations = [
            str(path.relative_to(ROOT))
            for path in APP.rglob("*.py")
            if "create_all(" in path.read_text(encoding="utf-8")
        ]

        self.assertEqual(
            violations,
            [],
            f"Schema creation must be handled only by Alembic: {violations}",
        )

    def test_repositories_do_not_commit_transactions(self) -> None:
        violations: list[str] = []

        for path in python_files(APP / "repositories"):
            if path.name == "unit_of_work.py":
                continue
            lines = commit_calls(path)
            if lines:
                violations.append(f"{path.name}: lines {lines}")

        self.assertEqual(
            violations,
            [],
            f"Transaction commits belong to UnitOfWork: {violations}",
        )
