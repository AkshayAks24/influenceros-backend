"""
Global exception handlers and helpers for consistent API error responses.
"""
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def raise_api_error(status_code: int, error_code: str, message: str):
    """
    Helper function to raise a consistent HTTPException.
    
    Example usage:
        raise_api_error(404, "user_not_found", "The requested user does not exist.")
    """
    raise HTTPException(
        status_code=status_code,
        detail={"error": error_code, "message": message},
    )


def setup_exception_handlers(app: FastAPI):
    """
    Registers global exception handlers for the FastAPI app.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Log the actual exception details for debugging, but don't leak it to the client
        logger.error(f"Unhandled server error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "Something went wrong",
            },
        )
