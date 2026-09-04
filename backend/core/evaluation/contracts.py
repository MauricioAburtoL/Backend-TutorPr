"""Contratos tipados de la primera iteración del evaluador flexible."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


ValueType = Literal[
    "integer",
    "number",
    "string",
    "boolean",
    "array",
    "tuple",
    "matrix",
]
InputSource = Literal["stdin", "literal_assignment"]
StdinLayout = Literal[
    "one_value_per_call",
    "single_line_tokens",
    "count_then_values",
    "values_then_blank",
]
CollectionFormat = Literal["literal", "joined_line", "per_line"]


class InputSlot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    value_type: ValueType = Field(alias="type")
    item_type: ValueType | None = None
    min_items: int | None = Field(default=None, ge=0)
    max_items: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_collection_shape(self):
        if self.value_type in {"array", "tuple", "matrix"} and self.item_type is None:
            raise ValueError("Las entradas de colección requieren item_type")
        if (
            self.min_items is not None
            and self.max_items is not None
            and self.min_items > self.max_items
        ):
            raise ValueError("min_items no puede ser mayor que max_items")
        return self


class InputDefinition(BaseModel):
    slots: List[InputSlot] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        ids = [slot.id for slot in self.slots]
        if len(ids) != len(set(ids)):
            raise ValueError("Los identificadores de entrada no pueden repetirse")
        return self


class AutoInputBinding(BaseModel):
    mode: Literal["auto"] = "auto"
    accepted_sources: List[InputSource] = Field(
        default_factory=lambda: ["stdin", "literal_assignment"],
        min_length=1,
    )
    stdin_layouts: List[StdinLayout] = Field(
        default_factory=lambda: ["one_value_per_call"],
        min_length=1,
    )
    max_literal_candidates: int = Field(default=8, ge=1, le=20)
    max_literal_mappings: int = Field(default=64, ge=1, le=500)
    # Presupuesto de latencia del enlace automático (`FR-BIND-008`).
    max_binding_seconds: float = Field(default=2.5, gt=0, le=10)
    ambiguity_policy: Literal["inconclusive"] = "inconclusive"


class OutputObservation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: Literal["stdout_events", "return_value", "object_state"] = (
        "stdout_events"
    )
    selection: Literal[
        "last_parseable",
        "unique_parseable",
        "return_value",
        "object_state",
    ] = "last_parseable"
    value_type: ValueType = Field(alias="type")
    item_type: ValueType | None = None
    allow_extra_output: bool = True
    absolute_tolerance: float = Field(default=1e-9, ge=0)
    relative_tolerance: float = Field(default=1e-9, ge=0)
    ambiguity_policy: Literal["inconclusive"] = "inconclusive"
    # Perfil lingüístico declarado para respuestas booleanas (`FR-OUT-008`).
    boolean_profile: Literal["strict", "negation_aware"] = "strict"
    boolean_keywords: List[str] = Field(default_factory=list)
    # Presentaciones aceptadas para resultados de tipo colección (`FR-OUT-007`).
    collection_formats: List[CollectionFormat] = Field(
        default_factory=lambda: ["literal"],
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_profiles(self):
        if self.boolean_profile == "negation_aware" and self.value_type != "boolean":
            raise ValueError(
                "boolean_profile solo aplica a observaciones de tipo boolean"
            )
        if self.boolean_keywords and self.boolean_profile == "strict":
            raise ValueError(
                "boolean_keywords requiere el perfil negation_aware"
            )
        return self


class ExpressionTreeOracle(BaseModel):
    kind: Literal["expression_tree"] = "expression_tree"
    expression: Dict[str, Any]


class ScenarioOracle(BaseModel):
    kind: Literal["scenario"] = "scenario"
    steps: List[Dict[str, Any]] = Field(min_length=1)


class ExpectedCasesOracle(BaseModel):
    kind: Literal["expected_cases"] = "expected_cases"


OracleDefinition = Annotated[
    Union[ExpressionTreeOracle, ScenarioOracle, ExpectedCasesOracle],
    Field(discriminator="kind"),
]


class VerificationCase(BaseModel):
    inputs: Dict[str, Any]
    visibility: Literal["visible", "hidden"] = "hidden"
    required: bool = True
    expected: Any | None = None


class VerificationDefinition(BaseModel):
    cases: List[VerificationCase] = Field(min_length=1)


class EvaluationLimits(BaseModel):
    execution_timeout_ms: int = Field(default=3000, ge=100, le=10_000)
    max_output_characters: int = Field(default=100_000, ge=100, le=100_000)
    max_input_requests: int = Field(default=20, ge=1, le=200)


class TargetDefinition(BaseModel):
    name_preference: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )
    parameter_count: int | None = Field(default=None, ge=0)
    return_type: ValueType | None = None


class EvaluationBase(BaseModel):
    inputs: InputDefinition
    input_binding: AutoInputBinding = Field(default_factory=AutoInputBinding)
    observation: OutputObservation
    oracle: OracleDefinition
    verification: VerificationDefinition
    limits: EvaluationLimits = Field(default_factory=EvaluationLimits)


class ScriptEvaluation(EvaluationBase):
    kind: Literal["script"] = "script"


class FunctionEvaluation(EvaluationBase):
    kind: Literal["function"] = "function"
    target: TargetDefinition


class ClassMethodEvaluation(EvaluationBase):
    kind: Literal["class_method"] = "class_method"
    target: TargetDefinition


EvaluationDefinition = Annotated[
    Union[ScriptEvaluation, FunctionEvaluation, ClassMethodEvaluation],
    Field(discriminator="kind"),
]


class ExerciseContractDefinition(BaseModel):
    schema_version: Literal[1] = 1
    exercise_id: str = Field(min_length=1)
    contract_version: int = Field(default=1, ge=1)
    evaluation: EvaluationDefinition

    @model_validator(mode="after")
    def validate_case_inputs(self):
        if (
            self.evaluation.kind in {"function", "class_method"}
            and self.evaluation.target.parameter_count is not None
            and self.evaluation.target.parameter_count
            != len(self.evaluation.inputs.slots)
        ):
            raise ValueError(
                "parameter_count debe coincidir con la cantidad de entradas lógicas"
            )
        if (
            self.evaluation.kind == "script"
            and self.evaluation.observation.source != "stdout_events"
        ):
            raise ValueError("La modalidad script debe observar stdout_events")
        if (
            self.evaluation.kind == "function"
            and self.evaluation.observation.source != "return_value"
        ):
            raise ValueError("La modalidad function debe observar return_value")

        slots_by_id = {slot.id: slot for slot in self.evaluation.inputs.slots}
        slot_ids = set(slots_by_id)
        for index, case in enumerate(self.evaluation.verification.cases, start=1):
            case_ids = set(case.inputs)
            if case_ids != slot_ids:
                missing = sorted(slot_ids - case_ids)
                unknown = sorted(case_ids - slot_ids)
                raise ValueError(
                    f"Caso {index} incompatible; faltantes={missing}, desconocidos={unknown}"
                )
            for input_id, value in case.inputs.items():
                if not _value_matches_slot(value, slots_by_id[input_id]):
                    raise ValueError(
                        f"Caso {index}: el valor de {input_id} no coincide con su tipo"
                    )
            if (
                self.evaluation.oracle.kind == "expected_cases"
                and case.expected is None
            ):
                raise ValueError(
                    "Los casos de expected_cases requieren un valor expected"
                )

        self._validate_oracle(slots_by_id)
        return self

    def _validate_oracle(self, slots_by_id) -> None:
        """Comprueba el oráculo antes de publicar el ejercicio (`FR-CON-005`).

        Un árbol con una operación inexistente o incompatible con los datos
        declarados debe rechazarse aquí y no descubrirse durante el intento de
        un estudiante.
        """
        if self.evaluation.oracle.kind != "expression_tree":
            return

        from .expression import OracleConfigurationError, evaluate_expression

        for index, case in enumerate(self.evaluation.verification.cases, start=1):
            try:
                evaluate_expression(self.evaluation.oracle.expression, case.inputs)
            except OracleConfigurationError as exc:
                raise ValueError(f"Oráculo inválido: {exc}") from exc
            except Exception as exc:  # noqa: BLE001
                raise ValueError(
                    f"El oráculo falló en el caso {index}: "
                    f"{exc.__class__.__name__}: {exc}"
                ) from exc


def _scalar_matches(value: Any, value_type: ValueType | None) -> bool:
    if value_type == "integer":
        return type(value) is int
    if value_type == "number":
        return type(value) in {int, float}
    if value_type == "string":
        return isinstance(value, str)
    if value_type == "boolean":
        return type(value) is bool
    return False


def _value_matches_slot(value: Any, slot: InputSlot) -> bool:
    if slot.value_type in {"integer", "number", "string", "boolean"}:
        return _scalar_matches(value, slot.value_type)
    if slot.value_type in {"array", "tuple"}:
        if not isinstance(value, (list, tuple)):
            return False
        if slot.min_items is not None and len(value) < slot.min_items:
            return False
        if slot.max_items is not None and len(value) > slot.max_items:
            return False
        return all(_scalar_matches(item, slot.item_type) for item in value)
    if slot.value_type == "matrix":
        return (
            isinstance(value, (list, tuple))
            and all(isinstance(row, (list, tuple)) for row in value)
            and all(
                _scalar_matches(item, slot.item_type)
                for row in value
                for item in row
            )
        )
    return False
