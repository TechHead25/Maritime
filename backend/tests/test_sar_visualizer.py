"""Tests for SAR Visualizer service and dynamic SAR image endpoints."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_sar_image_diagnostics_ennore():
    """Verify Ennore 2017 case generates valid diagnostics PNG."""
    resp = client.get("/api/cases/case_ennore_2017/sar-image?view=diagnostics")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.headers["x-case-id"] == "case_ennore_2017"
    assert len(resp.content) > 50000  # Substantial plot byte size


def test_sar_image_detection_ennore():
    """Verify Ennore 2017 case generates valid slick detection crop."""
    resp = client.get("/api/cases/case_ennore_2017/sar-image?view=detection")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 20000


def test_sar_image_new_diamond():
    """Verify New Diamond 2020 case generates distinct imagery from Ennore."""
    resp_nd = client.get("/api/cases/case_new_diamond_2020/sar-image?view=diagnostics")
    resp_en = client.get("/api/cases/case_ennore_2017/sar-image?view=diagnostics")
    assert resp_nd.status_code == 200
    assert resp_en.status_code == 200
    # Different cases have different coordinates and arrays, so bytes must differ
    assert resp_nd.content != resp_en.content


def test_sar_image_invalid_case():
    """Verify 404 is returned for non-existent case."""
    resp = client.get("/api/cases/invalid-case-id-xyz/sar-image")
    assert resp.status_code == 404
