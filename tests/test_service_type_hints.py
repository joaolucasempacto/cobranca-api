import ast
from pathlib import Path
from unittest import TestCase

SERVICES_DIR = Path(__file__).resolve().parents[1] / "app" / "services"


class ServiceTypeHintTests(TestCase):
    def test_service_methods_have_complete_type_hints(self) -> None:
        violations: list[str] = []

        for path in sorted(SERVICES_DIR.glob("*.py")):
            if path.name == "__init__.py":
                continue

            tree = ast.parse(path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                arguments = [
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                ]
                for argument in arguments:
                    if argument.arg in {"self", "cls"}:
                        continue
                    if argument.annotation is None:
                        violations.append(
                            f"{path.name}:{node.lineno} "
                            f"{node.name}() parameter '{argument.arg}'"
                        )

                if (
                    node.args.vararg is not None
                    and node.args.vararg.annotation is None
                ):
                    violations.append(
                        f"{path.name}:{node.lineno} "
                        f"{node.name}() variadic positional parameter"
                    )

                if (
                    node.args.kwarg is not None
                    and node.args.kwarg.annotation is None
                ):
                    violations.append(
                        f"{path.name}:{node.lineno} "
                        f"{node.name}() variadic keyword parameter"
                    )

                if node.returns is None:
                    violations.append(
                        f"{path.name}:{node.lineno} "
                        f"{node.name}() return type"
                    )

        self.assertEqual(
            violations,
            [],
            "Services must keep complete type hints: "
            + ", ".join(violations),
        )
