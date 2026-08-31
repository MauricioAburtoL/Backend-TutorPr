# # backend/schemas/__init__.py
# from .schemas import (
#     ExecuteIn,
#     HintIn, HintOut,
#     CodeIn, CFGOut,
#     ExecResult,  # si lo tienes
# )
# __all__ = [
#     "ExecuteIn", "ExecuteOut",
#     "HintIn", "HintOut",
#     "CodeIn", "CFGOut",
#     "ExecResult",
# ]

from .baseSchemas import Lang
from .executionSchemas import (
    ExecuteIn,
    ExecResult,
    CodeIn,
    CodeOnly,
    CFGOut,
    CFGRequest,
    TelemetryEventIn,
)
from .tutorSchemas import HintIn, HintOut
from .courseSchemas import ExerciseSchema, TopicSchema
from .userSchemas import UserStatsSchema, BehavioralMetrics, SkillSchema, LoginIn, LoginOut

__all__ = [
    "Lang",
    "ExecuteIn",
    "ExecResult",
    "CodeIn",
    "CodeOnly", # <--- Ahora sí está incluido
    "CFGOut",
    "CFGRequest",
    "TelemetryEventIn",
    "HintIn",
    "HintOut",
    "ExerciseSchema",
    "TopicSchema",
    "UserStatsSchema",
    "BehavioralMetrics",
    "SkillSchema",
    "LoginIn",
    "LoginOut"
]
