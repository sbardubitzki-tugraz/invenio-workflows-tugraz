# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Graz University of Technology.
#
# invenio-workflows-tugraz is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records jobs."""

from datetime import datetime

from invenio_i18n import lazy_gettext as _
from invenio_jobs.jobs import JobType, PredefinedArgsSchema
from invenio_jobs.models import Job

from marshmallow import fields

from .tasks import validate_records_dois

def check_input(var_in):
    return var_in if var_in is not None else False

class RecordsPredefinedArgsSchema(PredefinedArgsSchema):
    """Schema of input arguments for `ValidateRecordsDOIsJob`."""

    verbose = fields.Boolean(
        allow_none = True,
        dump_default = False,
        load_default = False,
        metadata={
            "description": _("Choose to get more detailed output in the logs."),
            "title": _("Verbose mode"),
        },
        #pre_load = check_input,
        required=False,
    )

    fix_urls = fields.Boolean(
        allow_none = True,
        dump_default = False,
        load_default = False,
        metadata={
            "description": _("Choose to automatically fix wrong URLs saved in DataCite."),
            "title": _("Fix URLs"),
        },
        #pre_load = check_input,
        required=False,
    )

    job_arg_schema = fields.String(
        metadata={"type": "hidden"},
        dump_default="RecordsPredefinedArgsSchema",
        load_default="RecordsPredefinedArgsSchema",
    )


class ValidateRecordsDOIsJob(JobType):
    """Job for validating URLs stored in DataCitefor each record with a DOI."""
    
    arguments_schema = RecordsPredefinedArgsSchema
    description = _("Validate DOIs of all records.")
    id = "validate_records_dois"
    task = validate_records_dois
    title = _("Validate Records DOIs")

    @classmethod
    def build_task_arguments(
        cls, 
        job_obj: Job,  # noqa: ARG003
        since: datetime | None = None,  # noqa: ARG003 
        **kwargs: dict | None  # noqa: ARG003
    ) -> dict:
        """Define extra arguments to be injected on task execution."""
        return {
            "verbose": kwargs.get("verbose") if kwargs.get("verbose") is not None else False,
            "fix_urls": kwargs.get("fix_urls") if kwargs.get("fix_urls") is not None else False,
            }

