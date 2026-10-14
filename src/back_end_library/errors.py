"""Erros da API com um código fixo, além da mensagem.

Toda resposta de erro sai como {"detail": "<mensagem em inglês>", "code": "<código>"}.
O front decide o texto pela chave "code" (que não muda), não pela mensagem (que pode mudar).
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, detail: str, headers: dict | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code


# erros que não passam por ApiError (rota inexistente, método errado...) ganham um código pelo status
STATUS_CODES = {
    400: "bad_request",
    401: "invalid_session",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "too_many_requests",
    503: "unavailable",
}


def install_error_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        code = getattr(exc, "code", None) or STATUS_CODES.get(exc.status_code, "error")
        return JSONResponse(
            {"detail": exc.detail, "code": code},
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # mesmo formato do FastAPI (lista de problemas por campo) + o código
        return JSONResponse({"detail": jsonable_encoder(exc.errors()), "code": "validation_error"}, status_code=422)
