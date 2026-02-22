import datetime
import asyncio
import os.path
from typing import Optional
from pydantic import BaseModel, Field

from app.services.tool_registry import ToolRegistry

# --- Schemas ---

class ListEventsSchema(BaseModel):
    count: int = Field(10, description="Number of upcoming events to list.")

class CreateEventSchema(BaseModel):
    summary: str = Field(..., description="Title of the event.")
    start_time: str = Field(..., description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or 'now'.")
    end_time: str = Field(..., description="End time in ISO format or duration like '30m', '1h'.")
    description: Optional[str] = Field(None, description="Description of the event.")
    location: Optional[str] = Field(None, description="Location of the event.")

class UpdateEventSchema(BaseModel):
    event_id: str = Field(..., description="ID of the event to update.")
    summary: Optional[str] = Field(None, description="New title.")
    start_time: Optional[str] = Field(None, description="New start time in ISO format.")
    end_time: Optional[str] = Field(None, description="New end time in ISO format.")
    description: Optional[str] = Field(None, description="New description.")

class DeleteEventSchema(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete.")

# --- Helpers ---

def _get_service():
    try:
        from googleapiclient.discovery import build
        from skills.google_calendar.auth import get_calendar_credentials
    except ImportError as e:
        raise RuntimeError(f"Google Calendar dependencies not installed: {e}")
    creds = get_calendar_credentials()
    if not creds:
        raise ValueError("Google Calendar credentials not found. Run 'setup_calendar_auth.py' first.")
    return build('calendar', 'v3', credentials=creds)

def _parse_time(time_str: str, base_time: datetime.datetime = None) -> datetime.datetime:
    if not base_time:
        base_time = datetime.datetime.now()
    if time_str.lower() == "now":
        return base_time
    if time_str.endswith('m'):
        try:
            return base_time + datetime.timedelta(minutes=int(time_str[:-1]))
        except ValueError:
            pass
    elif time_str.endswith('h'):
        try:
            return base_time + datetime.timedelta(hours=int(time_str[:-1]))
        except ValueError:
            pass
    try:
        return datetime.datetime.fromisoformat(time_str)
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str}. Use ISO (YYYY-MM-DDTHH:MM:SS) or relative (30m, 1h).")

# --- Async implementations ---

async def list_events_impl(count: int = 10) -> str:
    loop = asyncio.get_event_loop()
    def _sync():
        try:
            service = _get_service()
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=count, singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            if not events:
                return "Inga kommande händelser hittades."
            result = "Kommande kalenderhändelser:\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                result += f"- [{event['id']}] {start}: {event['summary']}\n"
            return result
        except Exception as e:
            return f"Fel vid hämtning av kalender: {e}"
    return await loop.run_in_executor(None, _sync)

async def create_event_impl(summary: str, start_time: str, end_time: str, description: str = None, location: str = None) -> str:
    loop = asyncio.get_event_loop()
    def _sync():
        try:
            service = _get_service()
            start_dt = _parse_time(start_time)
            end_dt = _parse_time(end_time, base_time=start_dt)
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Stockholm'},
                'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Stockholm'},
            }
            event = service.events().insert(calendarId='primary', body=event).execute()
            return f"Händelse skapad: {event.get('htmlLink')}"
        except Exception as e:
            return f"Fel vid skapande av händelse: {e}"
    return await loop.run_in_executor(None, _sync)

async def update_event_impl(event_id: str, summary: str = None, start_time: str = None, end_time: str = None, description: str = None) -> str:
    loop = asyncio.get_event_loop()
    def _sync():
        try:
            service = _get_service()
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if start_time:
                start_dt = _parse_time(start_time)
                event['start']['dateTime'] = start_dt.isoformat()
            if end_time:
                base = _parse_time(start_time) if start_time else datetime.datetime.fromisoformat(event['start']['dateTime'])
                end_dt = _parse_time(end_time, base_time=base)
                event['end']['dateTime'] = end_dt.isoformat()
            updated = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            return f"Händelse uppdaterad: {updated.get('htmlLink')}"
        except Exception as e:
            return f"Fel vid uppdatering av händelse: {e}"
    return await loop.run_in_executor(None, _sync)

async def delete_event_impl(event_id: str) -> str:
    loop = asyncio.get_event_loop()
    def _sync():
        try:
            service = _get_service()
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return "Händelse borttagen."
        except Exception as e:
            return f"Fel vid borttagning av händelse: {e}"
    return await loop.run_in_executor(None, _sync)

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    """Register Google Calendar tools."""

    registry.register(
        name="calendar_list",
        description="Lista kommande kalenderhändelser.",
        args_schema=ListEventsSchema,
    )(list_events_impl)

    registry.register(
        name="calendar_create",
        description="Skapa en ny kalenderhändelse.",
        args_schema=CreateEventSchema,
    )(create_event_impl)

    registry.register(
        name="calendar_update",
        description="Uppdatera en befintlig kalenderhändelse.",
        args_schema=UpdateEventSchema,
    )(update_event_impl)

    registry.register(
        name="calendar_delete",
        description="Ta bort en kalenderhändelse.",
        args_schema=DeleteEventSchema,
    )(delete_event_impl)
