from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import datetime


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationType(str, Enum):
    FORCITE_GEOMETRY_OPTIMIZATION = "forcite_geometry_optimization"
    FORCITE_DYNAMICS = "forcite_dynamics"
    FORCITE_ENERGY = "forcite_energy"
    FORCITE_ANNEAL = "forcite_anneal"
    CASTEP = "castep"
    DMOL3 = "dmol3"


@dataclass
class JobConfig:
    simulation_type: SimulationType
    name: str
    parameters: dict = field(default_factory=dict)
    structure_file: Optional[str] = None


@dataclass
class JobInfo:
    job_id: str
    config: JobConfig
    status: JobStatus = JobStatus.PENDING
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    completed_at: Optional[datetime.datetime] = None
    result_file: Optional[str] = None
    error_message: Optional[str] = None
