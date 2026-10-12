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


class task_execution_statistics:
    """Class to hold statistics for task execution."""

    def __init__(self):
        self.stat = {
            "total number": 0,
            "a DOI": 0,
            "DOI with wrong URL": 0,
            "DOI with fixed URL": 0,
            "DOI query errors": 0,
        }

    def accumulate(self, other: dict) -> None:
        """Accumulate statistics from another instance."""
        for key in self.stat.keys():
            self.stat[key] += other.get(key, 0)

    def failure(self) -> bool:
        """Get failure state."""
        return self.stat["DOI with wrong URL"] + self.stat["DOI query errors"] > 0
        
    def summary(self, record_type_name: str) -> str:
        """Return the statistics as a string."""
        msg = ""
        for key, value in self.stat.items():
            msg += f"{record_type_name} records with {key}: {value}\n"
        return msg


@shared_task
def validate_records_dois(
    verbose: bool | None = False,
    fix_urls: bool | None = False
) -> None:
    """Check URLs stored in DataCite for all records with a DOI."""

    client = DataCiteClient("datacite") # -> DataCiteRESTClient

    record_types = {
        "marc21": {"api": Marc21Record, "name" : "Publications" , "http_path": "publications", "statistics": task_execution_statistics()},
        "lom": {"api": LOMRecord, "name": "Educational Resources", "http_path": "oer", "statistics": task_execution_statistics()},
        "rdm": {"api": RDMRecord, "name": "Research Results", "http_path": "records", "statistics": task_execution_statistics()},
    }

    statistics_total = task_execution_statistics()

    for record_type in record_types.values():
        record_api = record_type.get("api")
        statistics = record_type.get("statistics")
        
        records = record_api.model_cls.query.all()

        statistics.stat["total number"] = len(records)

        for record in records:
            record_id = record.data.get('id', None)
            record_doi = record.data.get("pids", {}).get("doi", {}).get("identifier", None)

            if record_doi == None or record_doi == "":
                continue
            statistics.stat["a DOI"] += 1
            
            try:
                url_query = client.api.get_doi(record_doi) 
            except Exception as e:
                if verbose:
                    current_app.logger.warning(f"""
                        {record_type.get('name')} record ID {record_id} with DOI {record_doi} returned an error when validating: {str(e)}
                    """)
                statistics.stat["DOI query errors"] += 1
                continue

            url_expected = f"https://{current_app.config['APP_HOST']}/{record_type.get('http_path')}/{record_id}"
            if url_query != url_expected:
                if verbose:
                    current_app.logger.warning(f"""
                        {record_type.get('name')} record ID {record_id} with DOI {record_doi} has a wrong URL pointing to {url_query}, instead of {url_expected}.
                    """)

                wrong_url = True
                if fix_urls:
                    url_query = client.api.update_url(record_doi, url_expected)
                    if url_query == url_expected:
                        if verbose:
                            current_app.logger.info(f"""
                                {record_type.get('name')} record ID {record_id} with DOI {record_doi} has a fixed URL now pointing to {url_query}.
                            """)
                        wrong_url = False
                        statistics.stat["DOI with fixed URL"] += 1                        

                if wrong_url:
                    statistics.stat["DOI with wrong URL"] += 1


        current_app.logger.info(statistics.summary(record_type.get('name')))
        statistics_total.accumulate(statistics.stat)


    if statistics_total.failure():
        raise TaskExecutionPartialError(statistics_total.summary("Overall"))