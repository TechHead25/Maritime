"""Unit and Integration tests for Investigation PDF Report Generator."""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.case_service import case_service
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.report_generator import report_generator

client = TestClient(app)


def test_generate_pdf_report_for_historical_case():
    case_service.reload_cases_from_disk()
    assert "case_new_diamond_2020" in case_service.cases

    # Run pipeline to get result
    response = pipeline_service.run_pipeline("case_new_diamond_2020")
    assert response is not None

    output_pdf = "docs/test_investigation_report_new_diamond.pdf"
    res_path = report_generator.generate_pdf(response, output_path=output_pdf)

    assert os.path.exists(res_path)
    assert os.path.getsize(res_path) > 10000  # PDF should be at least 10KB with images and text

    # Verify header of PDF
    with open(res_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_api_download_investigation_report_pdf():
    case_service.reload_cases_from_disk()

    response = client.get("/api/cases/case_new_diamond_2020/report/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    assert len(response.content) > 10000


def test_api_download_investigation_report_alias():
    case_service.reload_cases_from_disk()

    response = client.get("/api/cases/case_new_diamond_2020/report")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    assert len(response.content) > 10000
