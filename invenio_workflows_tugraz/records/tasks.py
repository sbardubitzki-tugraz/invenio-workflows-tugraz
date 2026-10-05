# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 Graz University of Technology.
#
# invenio-workflows-tugraz is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records tasks."""

from celery import shared_task
from flask import current_app

@shared_task(ignore_result=True)
def validate_records_dois():
    current_app.logger.info("Starting DOI validation for all records...")
    return #?