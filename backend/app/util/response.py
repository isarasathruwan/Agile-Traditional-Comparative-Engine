from http import HTTPStatus
from typing import Generic, TypeVar

from fastapi import Response
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class GenericResponse(GenericModel, Generic[T]):
    status_code: int
    success: bool
    message: str
    error_code: str | None = None
    data: T | None = None

    @classmethod
    def success_response(
        cls, message: str, data: T | None = None, status_code: int = HTTPStatus.OK
    ) -> "GenericResponse[T]":
        return cls(status_code=status_code, success=True, message=message, data=data)

    @classmethod
    def failed_response(
        cls, message: str, error_code: str, status_code: int
    ) -> "GenericResponse[T]":
        return cls(
            status_code=status_code,
            success=False,
            message=message,
            error_code=error_code,
            data=None,
        )


class PaginatedResponse(GenericResponse[T], Generic[T]):
    page: int
    page_size: int
    total_records: int
    total_pages: int

    @classmethod
    def success_paginated_response(
        cls,
        message: str,
        data: T,
        page: int,
        page_size: int,
        total_records: int,
        status_code: int = HTTPStatus.OK,
    ) -> "PaginatedResponse[T]":
        total_pages = (total_records + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            status_code=status_code,
            success=True,
            message=message,
            data=data,
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
        )


def apply_status_code(response: Response, payload: GenericResponse[T]) -> GenericResponse[T]:
    response.status_code = payload.status_code
    return payload
