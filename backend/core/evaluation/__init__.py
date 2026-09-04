"""Motor versionado de evaluación flexible de ejercicios."""

from .contracts import ExerciseContractDefinition
from .engine import evaluate_flexible_exercise

__all__ = ["ExerciseContractDefinition", "evaluate_flexible_exercise"]

