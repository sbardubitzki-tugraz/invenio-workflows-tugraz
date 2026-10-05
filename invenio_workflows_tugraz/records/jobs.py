# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Graz University of Technology.
#
# invenio-workflows-tugraz is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records jobs."""

from invenio_jobs.jobs import JobType, PredefinedArgsSchema

from .tasks import validate_records_dois

class RecordsPredefinedArgsSchema(PredefinedArgsSchema):
    """Records Predefined Args Schema."""
    # to be completed
    pass

class ValidateRecordsDOIsJob(JobType):
    """Validate DOIs in records."""
    
    id = "validate_records_dois"
    title = "Validate Records DOIs"
    description = "Validate DOIs of all records."

    task = validate_records_dois

    arguments_schema = RecordsPredefinedArgsSchema