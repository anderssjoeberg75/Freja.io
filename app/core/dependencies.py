from app.core.logging import logger
from app.core.config import get_credential


class DependencyManager:
    """
    Manages singleton instances of tools and services.
    Replaces global variables in api.py.
    """

    def __init__(self):
        self._garmin_tool = None
        self._strava_tool = None
        self._withings_tool = None
        self._code_executor = None
        self._has_docker = False

        try:
            import app.tools.code_executor  # noqa: F401
            self._has_docker = True
        except ImportError:
            self._has_docker = False

    def get_garmin_tool(self):
        if self._garmin_tool:
            return self._garmin_tool

        garmin_email = get_credential("GARMIN_EMAIL")
        garmin_password = get_credential("GARMIN_PASSWORD")

        if garmin_email and garmin_password:
            try:
                from app.tools.garmin_core import GarminCoach

                self._garmin_tool = GarminCoach()
                logger.info("Garmin tool initialized (Dependency)")
            except Exception as exc:
                logger.error(f"Garmin init failed: {exc}")

        return self._garmin_tool

    def get_strava_tool(self):
        if self._strava_tool:
            return self._strava_tool

        strava_client_id = get_credential("STRAVA_CLIENT_ID")
        strava_refresh_token = get_credential("STRAVA_REFRESH_TOKEN")

        if strava_client_id and strava_refresh_token:
            try:
                from app.tools.strava_core import StravaTool

                self._strava_tool = StravaTool()
                logger.info("Strava tool initialized (Dependency)")
            except Exception as exc:
                logger.error(f"Strava init failed: {exc}")

        return self._strava_tool

    def get_withings_tool(self):
        if self._withings_tool:
            return self._withings_tool

        withings_client_id = get_credential("WITHINGS_CLIENT_ID")
        withings_client_secret = get_credential("WITHINGS_CLIENT_SECRET")

        if withings_client_id and withings_client_secret:
            try:
                from app.tools.withings_core import WithingsTool

                self._withings_tool = WithingsTool()
                logger.info("Withings tool initialized (Dependency)")
            except Exception as exc:
                logger.error(f"Withings init failed: {exc}")

        return self._withings_tool

    def get_code_executor(self):
        if self._code_executor:
            return self._code_executor

        if self._has_docker:
            try:
                from app.tools.code_executor import CodeExecutor

                self._code_executor = CodeExecutor()
                logger.info("CodeExecutor initialized (Dependency)")
            except Exception as exc:
                logger.error(f"CodeExecutor init failed: {exc}")

        return self._code_executor


_manager = DependencyManager()


def get_garmin():
    return _manager.get_garmin_tool()


def get_strava():
    return _manager.get_strava_tool()


def get_withings():
    return _manager.get_withings_tool()


def get_code_executor():
    return _manager.get_code_executor()
