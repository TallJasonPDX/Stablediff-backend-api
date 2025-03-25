
import os
from sqlalchemy import text
from fastapi import FastAPI
from typing import List, Tuple
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings
from app.database import engine

class StartupValidator:
    @staticmethod
    def check_environment_variables() -> List[Tuple[str, bool]]:
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'RUNPOD_API_KEY',
            'RUNPOD_ENDPOINT_ID'
        ]
        results = []
        for var in required_vars:
            exists = bool(os.getenv(var))
            results.append((var, exists))
        return results

    @staticmethod
    async def check_database_connection() -> bool:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError:
            return False

    @staticmethod
    async def validate_api_routes(app: FastAPI) -> List[Tuple[str, bool]]:
        results = []
        for route in app.routes:
            if route.path.startswith("/api"):
                results.append((route.path, True))
        return results

    @staticmethod
    async def run_all_checks(app: FastAPI) -> dict:
        env_checks = StartupValidator.check_environment_variables()
        db_check = await StartupValidator.check_database_connection()
        route_checks = await StartupValidator.validate_api_routes(app)
        
        return {
            "environment_variables": env_checks,
            "database_connection": db_check,
            "api_routes": route_checks
        }
