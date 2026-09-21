"""Operator-only sandbox reads, projected to exclude launch secrets and input values."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Annotated
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, ValidationError

from gateway import workflow_client as provider

basic = HTTPBasic(auto_error=False, scheme_name="PUGOperator", description="Use your existing PUG operator login. docusign credentials stay on the server.")


def operator(request: Request, credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)]):
    if credentials is None:
        provider.fail(401, "operator_login_required", "PUG operator login required.", {"WWW-Authenticate": 'Basic realm="PUG"'})
    try:
        path = os.environ["PUG_OPERATOR_HTPASSWD_FILE"]
        entries = [line.split(":", 1) for line in Path(path).read_text().splitlines() if line.strip()]
        if not entries or any(len(e) != 2 or not e[1].startswith(("$2a$", "$2b$", "$2y$")) for e in entries):
            raise ValueError("Invalid operator file")
        selected = next((h for user, h in entries if secrets.compare_digest(user.encode(), credentials.username.encode())), None)
        password = credentials.password.encode()
        # Perform a bcrypt check even for an unknown username.
        valid = bcrypt.checkpw(password, (selected or entries[0][1]).encode()) if len(password) <= 72 else False
    except (KeyError, OSError, ValueError):
        provider.fail(503, "operator_auth_not_configured", "Operator authentication is not configured correctly.")
    if selected is None or not valid:
        provider.fail(401, "operator_login_required", "Invalid PUG operator login.", {"WWW-Authenticate": 'Basic realm="PUG"'})

    request.state.audit_actor = credentials.username


def private_response(response: Response):
    response.headers["Cache-Control"] = "no-store"


class Workflow(BaseModel):
    id: UUID
    name: str | None = None
    status: str | None = None


class WorkflowList(BaseModel):
    environment: str = "sandbox"
    data: list[Workflow]


class InputField(BaseModel):
    field_name: str
    field_data_type: str


class Requirements(BaseModel):
    environment: str = "sandbox"
    workflow_id: UUID
    trigger_id: UUID | None = None
    trigger_event_type: str | None = None
    trigger_method: str | None = None
    trigger_input_schema: list[InputField]
    note: str = "Trigger input contract only; this may not describe all web-form fields. Launch URLs and default values are intentionally excluded."


class Instance(BaseModel):
    id: UUID
    name: str | None = None
    workflow_status: str | None = None
    template_id: UUID | None = None
    started_at: str | None = None
    ended_at: str | None = None
    last_modified_at: str | None = None
    total_steps: int | None = None
    last_completed_step: int | None = None
    last_completed_step_name: str | None = None


class Instances(BaseModel):
    environment: str = "sandbox"
    workflow_id: UUID
    data: list[Instance]


class InstanceDetail(BaseModel):
    environment: str = "sandbox"
    workflow_id: UUID
    data: Instance
    trigger_input_names: list[str] = Field(description="Input names only. Personal values, participant maps and execution URLs are omitted.")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail


router = APIRouter(prefix="/docusign/workflows", tags=["docusign workflows (read-only)"],
    dependencies=[Depends(operator), Depends(private_response)],
    responses={code: {"model": ErrorResponse, "description": desc} for code, desc in {
        401: "Operator login required", 403: "Provider access denied", 404: "Resource unavailable",
        429: "Provider rate limit", 502: "Provider or response failure", 503: "Configuration or docusign consent required",
        504: "Provider timeout",
    }.items()})


def validate(model, data):
    try:
        return model.model_validate(data)
    except ValidationError:
        provider.fail(502, "invalid_provider_response", "docusign workflow data does not match the expected contract.")


@router.get("", response_model=WorkflowList, operation_id="listDocusignWorkflows", summary="1. Discover available workflows")
def list_workflows():
    """Read workflows visible to PUG's configured sandbox account/user. Copy a returned id for steps 2–4. An empty data array is a valid result, not proof that a specific workflow is accessible. No workflow is started."""
    body = provider.get_json("")
    return validate(WorkflowList, {"data": body.get("data")})


@router.get("/{workflow_id}/requirements", response_model=Requirements, operation_id="getDocusignWorkflowRequirements", summary="2. Inspect API trigger inputs")
def requirements(workflow_id: UUID):
    """Returns input names/types for this workflow's API trigger. Does not open the public trigger link or create an instance. Web-form questions may be different from trigger inputs."""
    body = provider.get_json(f"/{workflow_id}/trigger-requirements")
    config = body.get("trigger_http_config") or {}
    if not isinstance(config, dict):
        provider.fail(502, "invalid_provider_response", "docusign returned invalid trigger configuration.")
    return validate(Requirements, {
        "workflow_id": workflow_id, "trigger_id": body.get("trigger_id"),
        "trigger_event_type": body.get("trigger_event_type"), "trigger_method": config.get("method"),
        "trigger_input_schema": body.get("trigger_input_schema"),
    })


@router.get("/{workflow_id}/instances", response_model=Instances, operation_id="listDocusignWorkflowInstances", summary="3. Inspect existing workflow runs")
def instances(workflow_id: UUID):
    """List existing runs and their state. Copy an instance id into step 4. Does not create test entries. Returns the provider collection without inventing undocumented pagination parameters."""
    body = provider.get_json(f"/{workflow_id}/instances")
    return validate(Instances, {"workflow_id": workflow_id, "data": body.get("data")})


@router.get("/{workflow_id}/instances/{instance_id}", response_model=InstanceDetail, operation_id="getDocusignWorkflowInstance", summary="4. Inspect one run")
def instance(workflow_id: UUID, instance_id: UUID):
    """Read status, timestamps, step progress and trigger input names. Excludes trigger values and execution links. This live provider read does not fabricate or persist a PUG inbound event."""
    body = provider.get_json(f"/{workflow_id}/instances/{instance_id}")
    inputs = body.get("trigger_inputs") or {}
    if not isinstance(inputs, dict):
        provider.fail(502, "invalid_provider_response", "docusign returned invalid trigger inputs.")
    return validate(InstanceDetail, {"workflow_id": workflow_id, "data": body, "trigger_input_names": sorted(inputs)})
