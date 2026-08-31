"""Pydantic input contracts and SDL result entities for Google Meet Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class AccountRefParams(BaseModel):
    account: str = Field("", description="Optional connected Google account email. Omit to use the active/only account.")


class DisconnectParams(BaseModel):
    account_id: str = Field(..., description="Connected Google account id to remove from Imperal.")


class ActivateAccountParams(BaseModel):
    email: str = Field(..., description="Email of the connected Google account to make active/default.")


# ---- Spaces ----

class CreateSpaceParams(AccountRefParams):
    access_type: str = Field("TRUSTED", description="Who can join without knocking: OPEN, TRUSTED, or RESTRICTED.")


class SpaceIdParams(AccountRefParams):
    space_name: str = Field(..., description="Meet space resource name, e.g. 'spaces/abcd-efgh-ijk'.")


class EndActiveConferenceParams(SpaceIdParams):
    pass


class UpdateSpaceConfigParams(SpaceIdParams):
    access_type: str = Field("", description="New access type: OPEN, TRUSTED, or RESTRICTED. Omit to leave unchanged.")


# ---- Conference records ----

class ListConferenceRecordsParams(AccountRefParams):
    space_name: str = Field("", description="Optional Meet space resource name to filter by, e.g. 'spaces/abcd-efgh-ijk'.")
    limit: int = Field(50, description="Max conference records to return (1-100).")


class ConferenceRecordIdParams(AccountRefParams):
    conference_record_name: str = Field(..., description="Conference record resource name, e.g. 'conferenceRecords/abc123'.")


class ListParticipantsParams(ConferenceRecordIdParams):
    limit: int = Field(50, description="Max participants to return (1-100).")


class ParticipantIdParams(ConferenceRecordIdParams):
    participant_name: str = Field(..., description="Participant resource name, e.g. 'conferenceRecords/abc123/participants/xyz'.")


class ListParticipantSessionsParams(ParticipantIdParams):
    limit: int = Field(50, description="Max participant sessions to return (1-100).")


# ---- Recordings & transcripts ----

class ListRecordingsParams(ConferenceRecordIdParams):
    limit: int = Field(50, description="Max recordings to return (1-100).")


class RecordingIdParams(ConferenceRecordIdParams):
    recording_name: str = Field(..., description="Recording resource name, e.g. 'conferenceRecords/abc123/recordings/xyz'.")


class ListTranscriptsParams(ConferenceRecordIdParams):
    limit: int = Field(50, description="Max transcripts to return (1-100).")


class TranscriptIdParams(ConferenceRecordIdParams):
    transcript_name: str = Field(..., description="Transcript resource name, e.g. 'conferenceRecords/abc123/transcripts/xyz'.")


class ListTranscriptEntriesParams(TranscriptIdParams):
    limit: int = Field(100, description="Max transcript entries (spoken lines) to return (1-500).")


# ---- Calendar-linked meetings ----

class CreateCalendarMeetingParams(AccountRefParams):
    summary: str = Field(..., description="Event title, e.g. 'Weekly sync'.")
    start_time: str = Field(..., description="ISO 8601 start datetime, e.g. '2026-09-01T10:00:00+03:00'.")
    end_time: str = Field(..., description="ISO 8601 end datetime, e.g. '2026-09-01T10:30:00+03:00'.")
    attendee_emails: list[str] = Field(default_factory=list, description="Attendee email addresses to invite.")
    description: str = Field("", description="Optional event description.")


class CalendarEventIdParams(AccountRefParams):
    event_id: str = Field(..., description="Google Calendar event id.")


class AuditParams(AccountRefParams):
    pass


# ---- SDL entities ----

class MeetAccount(sdl.Entity):
    id: str = ""
    title: str = ""
    account_id: str
    email: str
    is_active: bool


class AccountList(sdl.Entity):
    id: str = ""
    title: str = ""
    accounts: list[MeetAccount]


class MeetSpace(sdl.Entity):
    id: str = ""
    title: str = ""
    space_name: str
    meeting_uri: str
    meeting_code: str
    access_type: str


class ActiveConference(sdl.Entity):
    id: str = ""
    title: str = ""
    conference_record_name: str
    active: bool


class ConferenceRecord(sdl.Entity):
    id: str = ""
    title: str = ""
    conference_record_name: str
    space_name: str
    start_time: str
    end_time: str


class ConferenceRecordList(sdl.Entity):
    id: str = ""
    title: str = ""
    records: list[ConferenceRecord]


class Participant(sdl.Entity):
    id: str = ""
    title: str = ""
    participant_name: str
    display_name: str
    earliest_start_time: str
    latest_end_time: str


class ParticipantList(sdl.Entity):
    id: str = ""
    title: str = ""
    participants: list[Participant]


class ParticipantSession(sdl.Entity):
    id: str = ""
    title: str = ""
    session_name: str
    start_time: str
    end_time: str


class ParticipantSessionList(sdl.Entity):
    id: str = ""
    title: str = ""
    sessions: list[ParticipantSession]


class Recording(sdl.Entity):
    id: str = ""
    title: str = ""
    recording_name: str
    state: str
    export_uri: str


class RecordingList(sdl.Entity):
    id: str = ""
    title: str = ""
    recordings: list[Recording]


class Transcript(sdl.Entity):
    id: str = ""
    title: str = ""
    transcript_name: str
    state: str
    export_uri: str


class TranscriptList(sdl.Entity):
    id: str = ""
    title: str = ""
    transcripts: list[Transcript]


class TranscriptEntry(sdl.Entity):
    id: str = ""
    title: str = ""
    entry_name: str
    participant_name: str
    text: str
    start_time: str


class TranscriptEntryList(sdl.Entity):
    id: str = ""
    title: str = ""
    entries: list[TranscriptEntry]


class CalendarMeeting(sdl.Entity):
    id: str = ""
    title: str = ""
    event_id: str
    summary: str
    meet_link: str
    start_time: str
    end_time: str


class HealthAudit(sdl.Entity):
    id: str = ""
    title: str = ""
    connected_accounts: int
    recent_conference_count: int
    notes: list[str]


class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    deleted: bool
    id_value: str
