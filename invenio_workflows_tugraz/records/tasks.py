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

    record_apis = {
        "marc21": Marc21Record,
        "lom": LOMRecord,
        "rdm": RDMRecord,
    }

    http_folder = {
        "marc21": "publications",
        "lom": "oer",
        "rdm": "records",
    }


    nr_total_invalid_dois = 0  # Total number of invalid DOIs across all services
    for api in record_apis:
        record_api = record_apis.get(api)

        records = record_api.model_cls.query.all()
        current_app.logger.debug(f"Found {len(records)} {api.upper()} records to validate.")

        recs_without_doi = 0
        recs_with_doi = 0
        invalid_dois = []  # List to store invalid DOIs

        for record in records:
            record_id = record.data.get('id', None)
            current_app.logger.debug(f"Validating DOI for {api.upper()} record ID: {record_id}")

            record_doi = record.data.get("pids", {}).get("doi", {}).get("identifier", None)

            if record_doi == None or record_doi == "":
                current_app.logger.debug(f"{api.upper()} record ID {record_id} has no DOI.")
                recs_without_doi += 1
                continue
            
            recs_with_doi += 1
            
            try:
                url_query = client.api.get_doi(record_doi) # get url DOI is pointing to
            # except DataCiteNotFoundError:
            #     current_app.logger.error(f"Test DOI {test_id} not found in DataCite.")
            except Exception as e:
                current_app.logger.warning(f"{api.upper()} record ID {record_id} with DOI {record_doi} returned an error when validating: {str(e)}")
                invalid_dois.append(record_id)
                continue

            url_expected = f"https://{current_app.config['APP_HOST']}/{http_folder.get(api)}/{record_id}"
            if url_query != url_expected:
                current_app.logger.warning(f"{api.upper()} record ID {record_id} has DOI {record_doi} pointing to {url_query}, but expected {url_expected}.")
                invalid_dois.append(record_id)





        nr_total_invalid_dois += len(invalid_dois)
        
        current_app.logger.info(f"{api.upper()} records without DOIs: {recs_without_doi}")
        current_app.logger.info(f"{api.upper()} records with DOIs: {recs_with_doi}")
        # for rec in invalid_dois:
        #     current_app.logger.warning(f"Invalid DOI found in {api.upper()} record ID: {rec}")

    if nr_total_invalid_dois > 0:
        current_app.logger.warning(f"Total invalid DOIs found across all services: {nr_total_invalid_dois}")
        raise TaskExecutionPartialError(f"Total invalid DOIs found across all services: {nr_total_invalid_dois}")