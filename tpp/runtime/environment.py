from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TYPE_CHECKING

from tpp.core.ast_nodes import TypeAnnotation, UnionTypeAnnotation
from tpp.core.errors import ReturnSignal, RuntimeTppError, TppCallFrame
from tpp.core.types import check_type_or_raise, is_value_compatible_with_type
from tpp.core.utils import suggest_closest

if TYPE_CHECKING:
    from tpp.runtime.engine import RuntimeEngine


class LazyValue:
    """Lazily computed expression result cached on first read."""

    def __init__(self, resolver: Callable[[], Any]) -> None:
        self._resolver = resolver
        self._evaluated = False
        self._value: Any = None

    def value(self) -> Any:
        if not self._evaluated:
            self._value = self._resolver()
            self._evaluated = True
        return self._value


class Scope:
    def __init__(
        self,
        parent: Optional[Scope] = None,
        self_obj: Optional[TppInstance] = None,
        is_module_scope: bool = False,
    ) -> None:
        self.parent = parent
        self.values: dict[str, Any] = {}
        self.self_obj = self_obj
        self.is_module_scope = is_module_scope
        self.exported_names: set[str] = set()
        self.has_explicit_exports: bool = False

    def define(self, name: str, value: Any, is_export: bool = False) -> None:
        self.values[name] = value
        if is_export:
            self.has_explicit_exports = True
            self.exported_names.add(name)

    def mark_export(self, name: str) -> None:
        self.has_explicit_exports = True
        self.exported_names.add(name)

    def has_in_chain(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.self_obj is not None and name in self.self_obj.fields:
            return True
        if self.parent is not None:
            return self.parent.has_in_chain(name)
        return False

    def available_names(self) -> set[str]:
        names = set(self.values.keys())
        if self.self_obj is not None:
            names.update(self.self_obj.fields.keys())
        if self.parent is not None:
            names.update(self.parent.available_names())
        return names

    def _resolve_lazy(self, value: Any) -> Any:
        if isinstance(value, LazyValue):
            return value.value()
        return value

    def get(self, name: str, line: int) -> Any:
        if name in self.values:
            return self._resolve_lazy(self.values[name])
        if self.self_obj is not None and name in self.self_obj.fields:
            return self._resolve_lazy(self.self_obj.fields[name])
        if self.parent is not None:
            return self.parent.get(name, line)

        suggestion = suggest_closest(name, self.available_names())
        if suggestion:
            raise RuntimeTppError(f"I don't understand '{name}'.", line, suggestion=f"Did you mean '{suggestion}'?")
        raise RuntimeTppError(f"I don't understand '{name}'. Did you define it with 'let'?", line)

    def assign_existing(self, name: str, value: Any, line: int) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.self_obj is not None and name in self.self_obj.fields:
            self.self_obj.fields[name] = value
            return
        if self.parent is not None:
            self.parent.assign_existing(name, value, line)
            return

        suggestion = suggest_closest(name, self.available_names())
        if suggestion:
            raise RuntimeTppError(f"I don't understand '{name}'.", line, suggestion=f"Did you mean '{suggestion}'?")
        raise RuntimeTppError(
            f"I don't understand '{name}'.",
            line,
            fix_preview=f"let {name} be ...",
        )

    def to_eval_context(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.parent is not None:
            result.update(self.parent.to_eval_context())
        if self.self_obj is not None:
            result.update(self.self_obj.fields)
        for key, value in self.values.items():
            result[key] = self._resolve_lazy(value)
        return result


class TppFunction:
    def __init__(
        self,
        name: str,
        params: list[str],
        body: list[Any],
        closure: Scope,
        is_method: bool = False,
        return_type: Optional[TypeAnnotation | UnionTypeAnnotation] = None,
        param_types: Optional[dict[str, TypeAnnotation | UnionTypeAnnotation]] = None,
        param_defaults: Optional[dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
        self.is_method = is_method
        self.return_type = return_type
        self.param_types = param_types or {}
        self.param_defaults = param_defaults or {}

    def invoke(self, engine: RuntimeEngine, args: list[Any], line: int, self_obj: Optional[TppInstance] = None) -> Any:
        local_scope = Scope(parent=self.closure, self_obj=self_obj)

        # Handle defaults for omitted arguments
        eval_args = list(args)
        if len(eval_args) < len(self.params):
            for i in range(len(eval_args), len(self.params)):
                p_name = self.params[i]
                if p_name in self.param_defaults:
                    def_expr = self.param_defaults[p_name]
                    def_val = engine.evaluator.evaluate(def_expr, self.closure, line)
                    eval_args.append(def_val)
                else:
                    break

        if len(eval_args) != len(self.params):
            raise RuntimeTppError(
                f"'{self.name}' expected {len(self.params)} arguments but got {len(args)}.",
                line,
            )

        # Type checking on parameters if enabled
        for param, value in zip(self.params, eval_args):
            if engine.config.enforce_types and param in self.param_types:
                check_type_or_raise(value, self.param_types[param], param, line=line)
            local_scope.define(param, value)

        frame = TppCallFrame(function_name=self.name, line=line, file_path=getattr(engine, "current_file_path", None))
        engine.call_stack.append(frame)

        result = None
        try:
            engine.execute_block(self.body, local_scope)
        except ReturnSignal as signal:
            result = signal.value
        finally:
            if engine.call_stack and engine.call_stack[-1] == frame:
                engine.call_stack.pop()

        # Type checking on return value if enabled
        if engine.config.enforce_types and self.return_type is not None:
            check_type_or_raise(result, self.return_type, f"return value of '{self.name}'", line=line)

        return result


class BoundMethod:
    def __init__(self, instance: TppInstance, method: TppFunction) -> None:
        self.instance = instance
        self.method = method

    def invoke(self, engine: RuntimeEngine, args: list[Any], line: int) -> Any:
        return self.method.invoke(engine, args, line, self_obj=self.instance)


class TppClass:
    def __init__(self, name: str, init_method: Optional[TppFunction], methods: dict[str, TppFunction]) -> None:
        self.name = name
        self.init_method = init_method
        self.methods = methods

    def instantiate(self, engine: RuntimeEngine, args: list[Any], line: int) -> TppInstance:
        instance = TppInstance(self)
        if self.init_method is None:
            if args:
                raise RuntimeTppError(f"Class '{self.name}' does not accept constructor arguments.", line)
            return instance
        self.init_method.invoke(engine, args, line, self_obj=instance)
        return instance


class TppInstance:
    def __init__(self, klass: TppClass) -> None:
        self.klass = klass
        self.fields: dict[str, Any] = {}

    def resolve_member(self, name: str, line: int) -> Any:
        if name in self.fields:
            return self.fields[name]
        method = self.klass.methods.get(name)
        if method is not None:
            return BoundMethod(self, method)
        raise RuntimeTppError(f"'{self.klass.name}' has no member named '{name}'.", line)
