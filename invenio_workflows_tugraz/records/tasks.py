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

from datacite.errors import DataCiteNotFoundError
from invenio_jobs.errors import TaskExecutionPartialError
from invenio_rdm_records.records.api import RDMRecord
from invenio_rdm_records.services.pids.providers import DataCiteClient
from invenio_records_lom.records.api import LOMRecord
from invenio_records_marc21.records.api import Marc21Record



@shared_task(ignore_result=True)
def validate_records_dois():
    current_app.logger.info("Starting DOI validation for all records...")

    client = DataCiteClient("datacite") # -> DataCiteRESTClient

    record_types = {
        "marc21": {"api": Marc21Record, "name" : "Publications" , "http_path": "publications"},
        "lom": {"api": LOMRecord, "name": "Educational Resources", "http_path": "oer"},
        "rdm": {"api": RDMRecord, "name": "Research Results", "http_path": "records"},
    }

    for record_type in record_types.values():
        record_api = record_type.get("api")

        records = record_api.model_cls.query.all()

        record_type["all_records"] = len(records)
        record_type["records_with_doi"] = 0
        record_type["records_with_invalid_doi"] = 0
        record_type["records_with_doi_query_errors"] = 0

        for record in records:
            record_id = record.data.get('id', None)
            record_doi = record.data.get("pids", {}).get("doi", {}).get("identifier", None)

            if record_doi == None or record_doi == "":
                current_app.logger.debug(f"{record_type.get('name')} record ID {record_id} has no DOI.")
                continue
                
            record_type["records_with_doi"] += 1
            
            try:
                url_query = client.api.get_doi(record_doi) 
            except Exception as e:
                current_app.logger.warning(f"{record_type.get('name')} record ID {record_id} with DOI {record_doi} returned an error when validating: {str(e)}")
                record_type["records_with_doi_query_errors"] += 1
                continue

            url_expected = f"https://{current_app.config['APP_HOST']}/{record_type.get('http_path')}/{record_id}"
            if url_query != url_expected:
                current_app.logger.warning(f"{record_type.get('name')} record ID {record_id} has DOI {record_doi} pointing to {url_query}, but expected {url_expected}.")
                record_type["records_with_invalid_doi"] += 1


        # Log the results for the current record type
        current_app.logger.info(f"{record_type.get('name')} records total: {record_type['all_records']}")        
        current_app.logger.info(f"{record_type.get('name')} records with DOIs: {record_type['records_with_doi']}")
        current_app.logger.info(f"{record_type.get('name')} records with invalid DOIs: {record_type['records_with_invalid_doi']}")
        current_app.logger.info(f"{record_type.get('name')} records with DOI query errors: {record_type['records_with_doi_query_errors']}")

    # Calculate the total number of invalid DOIs and DOI query errors across all record types
    nr_total_invalid_dois = sum(record_types[record_type]["records_with_invalid_doi"] for record_type in record_types)
    nr_total_doi_query_errors = sum(record_types[record_type]["records_with_doi_query_errors"] for record_type in record_types) 
    if nr_total_invalid_dois + nr_total_doi_query_errors > 0:
        raise TaskExecutionPartialError(f"Total invalid DOIs across all records: {nr_total_invalid_dois}\nTotal DOI query errors across all records: {nr_total_doi_query_errors}")