import datetime
import os.path
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

from googleapiclient.discovery import build
from skills.google_calendar.auth import get_calendar_credentials

# --- Schemas ---

class ListEventsSchema(BaseModel):
    count: int = Field(10, description="Number of upcoming events to list.")

class CreateEventSchema(BaseModel):
    summary: str = Field(..., description="Title of the event.")
    start_time: str = Field(..., description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or 'now'.")
    end_time: str = Field(..., description="End time in ISO format (YYYY-MM-DDTHH:MM:SS) or duration in minutes (e.g., '30m', '1h').")
    description: Optional[str] = Field(None, description="Description of the event.")
    location: Optional[str] = Field(None, description="Location of the event.")

class UpdateEventSchema(BaseModel):
    event_id: str = Field(..., description="ID of the event to update.")
    summary: Optional[str] = Field(None, description="New title of the event.")
    start_time: Optional[str] = Field(None, description="New start time in ISO format.")
    end_time: Optional[str] = Field(None, description="New end time in ISO format.")
    description: Optional[str] = Field(None, description="New description.")

class DeleteEventSchema(BaseModel):
    event_id: str = Field(..., description="ID of the event to delete.")

# --- Helpers ---

def _get_service():
    creds = get_calendar_credentials()
    if not creds:
        raise ValueError("Google Calendar credentials not found. Run 'setup_calendar_auth.py' first.")
    return build('calendar', 'v3', credentials=creds)

def _parse_time(time_str: str, base_time: datetime.datetime = None) -> datetime.datetime:
    """Parses time string or relative duration."""
    if not base_time:
        base_time = datetime.datetime.now()

    if time_str.lower() == "now":
        return base_time
    
    # Check for relative duration (e.g., '30m', '1h') - usually for end_time based on start_time
    if time_str.endswith('m'):
        try:
            minutes = int(time_str[:-1])
            return base_time + datetime.timedelta(minutes=minutes)
        except ValueError:
            pass
    elif time_str.endswith('h'):
         try:
            hours = int(time_str[:-1])
            return base_time + datetime.timedelta(hours=hours)
         except ValueError:
            pass
            
    # Try ISO format
    try:
        return datetime.datetime.fromisoformat(time_str)
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str}. Use ISO (YYYY-MM-DDTHH:MM:SS) or relative (30m, 1h).")

# --- Implementations ---

def list_events_impl(count: int = 10) -> str:
    """Lists upcoming events from the primary calendar."""
    try:
        service = _get_service()
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=count, singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found."

        result = "Upcoming Events:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            result += f"- [{event['id']}] {start}: {event['summary']}\n"
            
        return result
    except Exception as e:
        return f"Error listing events: {e}"

def create_event_impl(summary: str, start_time: str, end_time: str, description: str = None, location: str = None) -> str:
    """Creates a new event."""
    try:
        service = _get_service()
        
        start_dt = _parse_time(start_time)
        end_dt = _parse_time(end_time, base_time=start_dt)
        
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Europe/Stockholm', # Defaulting to likely timezone, should be config
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Europe/Stockholm',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created: {event.get('htmlLink')}"
    except Exception as e:
        return f"Error creating event: {e}"

def update_event_impl(event_id: str, summary: str = None, start_time: str = None, end_time: str = None, description: str = None) -> str:
    """Updates an existing event."""
    try:
        service = _get_service()
        
        # First retrieve the event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if summary:
            event['summary'] = summary
        
        if description:
            event['description'] = description
            
        if start_time:
             start_dt = _parse_time(start_time)
             event['start']['dateTime'] = start_dt.isoformat()
             # If start changed but no end specified, keep original duration? 
             # For simplicity, if end is not provided, we might leave it (risking negative duration)
             # or require end if start changes.
             # Let's assume user provides both if shifting time, or just content updates.
        
        if end_time:
             # If we have a new start time, use it as base. Otherwise parse absolute or error.
             base = _parse_time(start_time) if start_time else datetime.datetime.fromisoformat(event['start']['dateTime'])
             end_dt = _parse_time(end_time, base_time=base)
             event['end']['dateTime'] = end_dt.isoformat()

        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return f"Event updated: {updated_event.get('htmlLink')}"
        
    except Exception as e:
        return f"Error updating event: {e}"

def delete_event_impl(event_id: str) -> str:
    """Deletes an event."""
    try:
        service = _get_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return "Event deleted."
    except Exception as e:
        return f"Error deleting event: {e}"

# --- Registration ---

from app.services.tool_registry import ToolRegistry

def register_tools(registry: ToolRegistry) -> None:
    """Register Google Calendar tools."""
    
    registry.register(
        name="calendar_list",
        description="Lists upcoming calendar events.",
        args_schema=ListEventsSchema,
    )(list_events_impl)

    registry.register(
        name="calendar_create",
        description="Creates a new calendar event.",
        args_schema=CreateEventSchema,
    )(create_event_impl)

    registry.register(
        name="calendar_update",
        description="Updates an existing calendar event.",
        args_schema=UpdateEventSchema,
    )(update_event_impl)

    registry.register(
        name="calendar_delete",
        description="Deletes a calendar event.",
        args_schema=DeleteEventSchema,
    )(delete_event_impl)
