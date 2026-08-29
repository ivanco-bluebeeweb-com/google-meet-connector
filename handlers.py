"""Chat functions for Google Meet Connector (Google Meet REST API v2 + Calendar v3)."""
from __future__ import annotations

from imperal_sdk import ActionResult

import accounts as ac
import meet_client as mc
from app import chat
from schemas import (
    AccountList, ActivateAccountParams, ActiveConference, AuditParams,
    CalendarEventIdParams, CalendarMeeting, ConferenceRecord,
    ConferenceRecordIdParams, ConferenceRecordList, CreateCalendarMeetingParams,
    CreateSpaceParams, DeleteResult, DisconnectParams,
    EndActiveConferenceParams, HealthAudit, ListConferenceRecordsParams,
    ListParticipantSessionsParams, ListParticipantsParams,
    ListRecordingsParams, ListTranscriptEntriesParams, ListTranscriptsParams,
    MeetAccount, MeetSpace, NoParams, Participant, ParticipantIdParams,
    ParticipantList, ParticipantSession, ParticipantSessionList, Recording,
    RecordingIdParams, RecordingList, SpaceIdParams, Transcript,
    TranscriptEntry, TranscriptEntryList, TranscriptIdParams,
    TranscriptList, UpdateSpaceConfigParams,
)

_SETTINGS = ac.SETTINGS


async def _get_account_or_error(ctx, account_ref: str):
    found = await ac.resolve_account(ctx, account_ref)
    if not found.get("ok"):
        return None, ActionResult.error(found.get("error") or "No Google account connected.")
    return found["account"], None


@chat.function(
    name="list_connections", action_type="read", data_model=AccountList,
    description="List the connected Google accounts and whether each still works.",
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    docs = await ac.all_accounts(ctx)
    items = [MeetAccount(account_id=d.id, email=ac.account_email(d) or ac.account_label(d),
                          is_active=bool((d.data or {}).get("is_active"))) for d in docs]
    return ActionResult.success(AccountList(accounts=items), summary=f"{len(items)} connected account(s).")


@chat.function(
    name="disconnect_account", action_type="destructive",
    description="Disconnect a Google account from Google Meet. Nothing in Google is changed; this only removes Imperal's saved token.",
)
async def disconnect_account(ctx, params: DisconnectParams) -> ActionResult:
    out = await ac.disconnect(ctx, params.account_id)
    if not out.get("ok"):
        return ActionResult.error(out.get("error") or "Could not disconnect that account.")
    return ActionResult.success(DeleteResult(deleted=True, id_value=params.account_id), summary=f"Disconnected {out.get('label', '')}.")


@chat.function(
    name="switch_account", action_type="write",
    description="Change the active Google account used by default for subsequent calls.",
)
async def switch_account(ctx, params: ActivateAccountParams) -> ActionResult:
    out = await ac.activate(ctx, params.email)
    if not out.get("ok"):
        return ActionResult.error(out.get("error") or "Could not switch account.")
    return ActionResult.success(MeetAccount(account_id=out["account"].id, email=ac.account_email(out["account"]), is_active=True), summary="Active account switched.")


# ---- Spaces ----

@chat.function(
    name="create_space", action_type="write", data_model=MeetSpace,
    description="Create a new Google Meet space -- a reusable meeting room with a stable link, not a one-off calendar event.",
)
async def create_space(ctx, params: CreateSpaceParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    body = {"config": {"accessType": params.access_type}}
    out = await mc.request(ctx, account, "POST", f"{mc.MEET_API}/spaces", json_body=body)
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    return ActionResult.success(MeetSpace(
        space_name=d.get("name", ""), meeting_uri=d.get("meetingUri", ""),
        meeting_code=d.get("meetingCode", ""), access_type=(d.get("config") or {}).get("accessType", ""),
    ), summary="Meet space created.")


@chat.function(
    name="get_space", action_type="read", data_model=MeetSpace,
    description="Read one Google Meet space in full by its resource name.",
)
async def get_space(ctx, params: SpaceIdParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.space_name}")
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    return ActionResult.success(MeetSpace(
        space_name=d.get("name", ""), meeting_uri=d.get("meetingUri", ""),
        meeting_code=d.get("meetingCode", ""), access_type=(d.get("config") or {}).get("accessType", ""),
    ))


@chat.function(
    name="update_space_config", action_type="write", data_model=MeetSpace,
    description="Update a Meet space's access type (who can join without knocking).",
)
async def update_space_config(ctx, params: UpdateSpaceConfigParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    if not params.access_type:
        return ActionResult.error("Nothing to update -- provide access_type.")
    body = {"config": {"accessType": params.access_type}}
    out = await mc.request(ctx, account, "PATCH", f"{mc.MEET_API}/{params.space_name}",
                            json_body=body, params={"updateMask": "config.accessType"})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    return ActionResult.success(MeetSpace(
        space_name=d.get("name", ""), meeting_uri=d.get("meetingUri", ""),
        meeting_code=d.get("meetingCode", ""), access_type=(d.get("config") or {}).get("accessType", ""),
    ), summary="Space config updated.")


@chat.function(
    name="end_active_conference", action_type="destructive",
    description="End the currently active conference in a Meet space, if one is running.",
)
async def end_active_conference(ctx, params: EndActiveConferenceParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "POST", f"{mc.MEET_API}/{params.space_name}:endActiveConference")
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    return ActionResult.success(ActiveConference(conference_record_name="", active=False), summary="Active conference ended.")


# ---- Conference records ----

@chat.function(
    name="list_conference_records", action_type="read", data_model=ConferenceRecordList,
    description="List conference records (past/ongoing meetings), optionally filtered to one space.",
)
async def list_conference_records(ctx, params: ListConferenceRecordsParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    q = {"pageSize": min(max(params.limit, 1), 100)}
    if params.space_name:
        q["filter"] = f"space.name = \"{params.space_name}\""
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/conferenceRecords", params=q)
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    items = [ConferenceRecord(conference_record_name=r.get("name", ""), space_name=r.get("space", ""),
                               start_time=r.get("startTime", ""), end_time=r.get("endTime", ""))
             for r in out["data"].get("conferenceRecords", [])]
    return ActionResult.success(ConferenceRecordList(records=items), summary=f"{len(items)} conference record(s).")


@chat.function(
    name="get_conference_record", action_type="read", data_model=ConferenceRecord,
    description="Read one conference record in full by its resource name.",
)
async def get_conference_record(ctx, params: ConferenceRecordIdParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.conference_record_name}")
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    return ActionResult.success(ConferenceRecord(conference_record_name=d.get("name", ""), space_name=d.get("space", ""),
                                                   start_time=d.get("startTime", ""), end_time=d.get("endTime", "")))


@chat.function(
    name="list_participants", action_type="read", data_model=ParticipantList,
    description="List participants who joined one conference record.",
)
async def list_participants(ctx, params: ListParticipantsParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.conference_record_name}/participants",
                            params={"pageSize": min(max(params.limit, 1), 100)})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    items = []
    for p in out["data"].get("participants", []):
        anon = p.get("anonymousUser") or {}
        signed = p.get("signedinUser") or {}
        items.append(Participant(participant_name=p.get("name", ""),
                                  display_name=signed.get("displayName") or anon.get("displayName", ""),
                                  earliest_start_time=p.get("earliestStartTime", ""),
                                  latest_end_time=p.get("latestEndTime", "")))
    return ActionResult.success(ParticipantList(participants=items), summary=f"{len(items)} participant(s).")


@chat.function(
    name="list_participant_sessions", action_type="read", data_model=ParticipantSessionList,
    description="List the individual join/leave sessions of one participant (a participant can rejoin several times).",
)
async def list_participant_sessions(ctx, params: ListParticipantSessionsParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.participant_name}/participantSessions",
                            params={"pageSize": min(max(params.limit, 1), 100)})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    items = [ParticipantSession(session_name=s.get("name", ""), start_time=s.get("startTime", ""), end_time=s.get("endTime", ""))
             for s in out["data"].get("participantSessions", [])]
    return ActionResult.success(ParticipantSessionList(sessions=items), summary=f"{len(items)} session(s).")


# ---- Recordings & transcripts ----

@chat.function(
    name="list_recordings", action_type="read", data_model=RecordingList,
    description="List cloud recordings for one conference record (requires a Workspace plan with Meet recording enabled).",
)
async def list_recordings(ctx, params: ListRecordingsParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.conference_record_name}/recordings",
                            params={"pageSize": min(max(params.limit, 1), 100)})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    items = [Recording(recording_name=r.get("name", ""), state=r.get("state", ""),
                        export_uri=(r.get("driveDestination") or {}).get("exportUri", ""))
             for r in out["data"].get("recordings", [])]
    return ActionResult.success(RecordingList(recordings=items), summary=f"{len(items)} recording(s).")


@chat.function(
    name="get_recording", action_type="read", data_model=Recording,
    description="Read one cloud recording in full by its resource name.",
)
async def get_recording(ctx, params: RecordingIdParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.recording_name}")
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    return ActionResult.success(Recording(recording_name=d.get("name", ""), state=d.get("state", ""),
                                            export_uri=(d.get("driveDestination") or {}).get("exportUri", "")))


@chat.function(
    name="list_transcripts", action_type="read", data_model=TranscriptList,
    description="List transcripts for one conference record (requires a Workspace plan with Meet transcription enabled).",
)
async def list_transcripts(ctx, params: ListTranscriptsParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.conference_record_name}/transcripts",
                            params={"pageSize": min(max(params.limit, 1), 100)})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    items = [Transcript(transcript_name=t.get("name", ""), state=t.get("state", ""),
                         export_uri=(t.get("docsDestination") or {}).get("exportUri", ""))
             for t in out["data"].get("transcripts", [])]
    return ActionResult.success(TranscriptList(transcripts=items), summary=f"{len(items)} transcript(s).")


@chat.function(
    name="get_transcript", action_type="read", data_model=Transcript,
    description="Read one transcript in full by its resource name.",
)
async def get_transcript(ctx, params: TranscriptIdParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.transcript_name}")
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    return ActionResult.success(Transcript(transcript_name=d.get("name", ""), state=d.get("state", ""),
                                             export_uri=(d.get("docsDestination") or {}).get("exportUri", "")))


@chat.function(
    name="list_transcript_entries", action_type="read", data_model=TranscriptEntryList,
    description="List individual spoken-line entries of one transcript.",
)
async def list_transcript_entries(ctx, params: ListTranscriptEntriesParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/{params.transcript_name}/entries",
                            params={"pageSize": min(max(params.limit, 1), 500)})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    items = [TranscriptEntry(entry_name=e.get("name", ""), participant_name=e.get("participant", ""),
                              text=e.get("text", ""), start_time=e.get("startTime", ""))
             for e in out["data"].get("transcriptEntries", [])]
    return ActionResult.success(TranscriptEntryList(entries=items), summary=f"{len(items)} transcript entr(y/ies).")


# ---- Calendar-linked meetings ----

@chat.function(
    name="create_calendar_meeting", action_type="write", data_model=CalendarMeeting,
    description="Create a Google Calendar event with an automatic Google Meet link attached -- the practical way to schedule a meeting without full Meet-API-only access.",
)
async def create_calendar_meeting(ctx, params: CreateCalendarMeetingParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    body = {
        "summary": params.summary,
        "description": params.description,
        "start": {"dateTime": params.start_time},
        "end": {"dateTime": params.end_time},
        "attendees": [{"email": e} for e in params.attendee_emails],
        "conferenceData": {"createRequest": {"requestId": params.summary[:40] or "meet-request",
                                              "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
    }
    out = await mc.request(ctx, account, "POST", f"{mc.CALENDAR_API}/calendars/primary/events",
                            json_body=body, params={"conferenceDataVersion": 1, "sendUpdates": "all"})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    conf = (d.get("conferenceData") or {}).get("entryPoints") or []
    meet_link = next((e.get("uri", "") for e in conf if e.get("entryPointType") == "video"), "")
    return ActionResult.success(CalendarMeeting(
        event_id=d.get("id", ""), summary=d.get("summary", ""), meet_link=meet_link,
        start_time=(d.get("start") or {}).get("dateTime", ""), end_time=(d.get("end") or {}).get("dateTime", ""),
    ), summary="Calendar event with Meet link created.")


@chat.function(
    name="get_calendar_meeting", action_type="read", data_model=CalendarMeeting,
    description="Read one Calendar event (with its Meet link, if any) in full by its event id.",
)
async def get_calendar_meeting(ctx, params: CalendarEventIdParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "GET", f"{mc.CALENDAR_API}/calendars/primary/events/{params.event_id}")
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    d = out["data"]
    conf = (d.get("conferenceData") or {}).get("entryPoints") or []
    meet_link = next((e.get("uri", "") for e in conf if e.get("entryPointType") == "video"), "")
    return ActionResult.success(CalendarMeeting(
        event_id=d.get("id", ""), summary=d.get("summary", ""), meet_link=meet_link,
        start_time=(d.get("start") or {}).get("dateTime", ""), end_time=(d.get("end") or {}).get("dateTime", ""),
    ))


@chat.function(
    name="cancel_calendar_meeting", action_type="destructive",
    description="Cancel (delete) a Calendar event that has a Meet link attached.",
)
async def cancel_calendar_meeting(ctx, params: CalendarEventIdParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    out = await mc.request(ctx, account, "DELETE", f"{mc.CALENDAR_API}/calendars/primary/events/{params.event_id}",
                            params={"sendUpdates": "all"})
    if not out.get("ok"):
        return ActionResult.error(mc.friendly(out))
    return ActionResult.success(DeleteResult(deleted=True, id_value=params.event_id), summary="Meeting cancelled.")


# ---- Audit ----

@chat.function(
    name="audit_meet_usage", action_type="read", data_model=HealthAudit,
    description="Value-add report: one-glance snapshot of connected accounts and recent conference activity.",
)
async def audit_meet_usage(ctx, params: AuditParams) -> ActionResult:
    account, err = await _get_account_or_error(ctx, params.account)
    if err:
        return err
    notes: list[str] = []
    out = await mc.request(ctx, account, "GET", f"{mc.MEET_API}/conferenceRecords", params={"pageSize": 25})
    recent = 0
    if out.get("ok"):
        recent = len(out["data"].get("conferenceRecords", []))
    else:
        notes.append("Could not read conference records: " + mc.friendly(out))
    docs = await ac.all_accounts(ctx)
    return ActionResult.success(HealthAudit(connected_accounts=len(docs), recent_conference_count=recent, notes=notes),
                                 summary=f"{len(docs)} account(s), {recent} recent conference record(s).")
