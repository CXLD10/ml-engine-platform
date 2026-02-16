from dataclasses import dataclass
from typing import Any


@dataclass
class ServiceError(Exception):
    error: str
    details: Any
    status_code: int


class UpstreamServiceError(ServiceError):
    pass


class DataValidationError(ServiceError):
    pass
