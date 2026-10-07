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

from invenio_access.permissions import system_identity
from invenio_jobs.errors import TaskExecutionPartialError
from repository_cli.utils import get_records_service

@shared_task(ignore_result=True)
def validate_records_dois():
    current_app.logger.info("Starting DOI validation for all records...")

    services = ["marc21", "lom", "rdm"]  # List of services to validate
    nr_total_invalid_dois = 0  # Total number of invalid DOIs across all services
    for service in services:
        records_service = get_records_service(service)
        records = records_service.read_all(identity=system_identity, fields=None)
        
        current_app.logger.debug(f"Found {len(records)} {service.upper()} records to validate.")

        recs_without_doi = 0
        recs_with_doi = 0
        nr_valid_dois = 0
        invalid_dois = []  # List to store invalid DOIs

        for record in records:
            record_id = record.get('id', None)
            current_app.logger.debug(f"Validating DOI for {service.upper()} record ID: {record_id}")

            ids = record.get("metadata", {}).get("identifiers", [])
            if ids == None or len(ids) == 0:
                current_app.logger.debug(f"{service.upper()} record ID {record_id} has no identifiers.")
                recs_without_doi += 1
                continue

            doi_valid = False
            for id in ids:
                if id.get("scheme") == "doi":
                    # do DOI validation here
                    # ... todo
                    recs_with_doi += 1
                    break
            
            if doi_valid:
                nr_valid_dois += 1
            else:
                invalid_dois.append(record_id)
                current_app.logger.debug(f"{service.upper()} record ID {record_id} has an invalid DOI.")

        nr_total_invalid_dois += len(invalid_dois)
        
        current_app.logger.info(f"{service.upper()} records without DOIs: {recs_without_doi}")
        current_app.logger.info(f"{service.upper()} records with DOIs: {recs_with_doi}")
        current_app.logger.info(f"{service.upper()} records with valid DOIs: {nr_valid_dois}")
        for rec in invalid_dois:
            current_app.logger.warning(f"Invalid DOI found in {service.upper()} record ID: {rec}")

    if nr_total_invalid_dois > 0:
        current_app.logger.warning(f"Total invalid DOIs found across all services: {nr_total_invalid_dois}")
        raise TaskExecutionPartialError(f"Total invalid DOIs found across all services: {nr_total_invalid_dois}")