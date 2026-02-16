from dataclasses import dataclass


@dataclass
class UpstreamServiceError(Exception):
    message: str


@dataclass
class DataValidationError(Exception):
    message: str
