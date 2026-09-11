from typing import Generic, TypeVar, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class ServiceStatus(BaseModel):
    api: str
    database: str
    vector_store: str


class HealthResponse(BaseModel):
    status: str
    project: str
    team: str
    problem_statement: str
    version: str
    services: ServiceStatus
    details: Optional[Dict[str, Any]] = None
