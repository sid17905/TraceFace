"""End-to-end API smoke tests that stub the network-bound OSINT stage.

These verify the FastAPI orchestration — upload -> vision -> streaming job ->
Merkle seal -> IPFS pin -> simulated blockchain anchor — without launching a
real Playwright browser or hitting the network. The heavy InsightFace models
DO load (once), and the liveness threshold is relaxed so the bundled sample
image passes the deepfake gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_inputs" / "sample_target.jpg"


@pytest.fixture(scope="module")
def client():
    import api.dependencies as deps

    vp = deps.get_vision_pipeline()
    vp.liveness.threshold = 999.0  # bypass deepfake gate for the sample image

    from api.main import app

    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "traceface-api"


def test_scan_upload_no_osint(client):
    with SAMPLE.open("rb") as f:
        r = client.post(
            "/api/v1/scan/upload?run_osint=false",
            files={"file": ("t.jpg", f, "image/jpeg")},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["osint_started"] is False
    scan = body["scan"]
    assert len(scan["embedding_vector"]) == 512
    assert scan["perceptual_hash_phash"]
    assert scan["embedding_hash_keccak256"].startswith("0x")
    assert len(scan["bounding_box"]["landmarks_5pt"]) == 5


def _stub_osint(monkeypatch, img: bytes) -> None:
    """Patch discovery + download + parser so OSINT resolves offline to one match."""

    from src.osint import dispatcher as disp_mod
    from src.osint import media_downloader as dl_mod
    from src.osint import social_parsers as sp_mod
    from src.osint.media_downloader import DownloadedMedia
    from src.osint.models import SearchCandidate, SearchEngine

    def fake_discover(self, query):
        cand = SearchCandidate(
            source_url="https://x.com/creator/status/1780",
            source_title="Original post",
            media_url="https://x.com/m.jpg",
            platform="twitter",
            engine=SearchEngine.GOOGLE_LENS_SERPAPI,
        )
        return [cand], SearchEngine.GOOGLE_LENS_SERPAPI

    def fake_fetch(self, url):
        return DownloadedMedia(
            url=url, data=img, content_type="image/jpeg", sha256=hashlib.sha256(img).hexdigest()
        )

    monkeypatch.setattr(disp_mod.OSINTDispatcher, "discover", fake_discover)
    monkeypatch.setattr(dl_mod.MediaDownloader, "fetch", fake_fetch)
    monkeypatch.setattr(sp_mod, "parse_post", lambda url: None)


def _stub_blockchain_and_ipfs(monkeypatch) -> None:
    """Patch blockchain and IPFS to return simulated successful responses."""

    from src.blockchain import client as bc_mod
    from src.storage import ipfs_client as ipfs_mod

    def fake_is_connected(self):
        return True

    def fake_register_provenance(self, record_hash, ipfs_cid, face_vector_hash):
        return {
            "status": "success",
            "tx_hash": "0x" + "a" * 64,
            "record_hash": record_hash,
            "ipfs_cid": ipfs_cid,
        }

    def fake_pin_json(self, payload):
        return "bafybei" + "a" * 50

    monkeypatch.setattr(bc_mod.BlockchainClient, "is_connected", fake_is_connected)
    monkeypatch.setattr(bc_mod.BlockchainClient, "register_provenance", fake_register_provenance)
    monkeypatch.setattr(ipfs_mod.IPFSClient, "pin_json", fake_pin_json)


def test_scan_upload_launches_job(client, monkeypatch):
    """The upload endpoint returns a real scan + a job handle when OSINT is on."""

    _stub_osint(monkeypatch, SAMPLE.read_bytes())

    with SAMPLE.open("rb") as f:
        r = client.post(
            "/api/v1/scan/upload?run_osint=true",
            files={"file": ("t.jpg", f, "image/jpeg")},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["osint_started"] is True
    assert body["job_id"].startswith("job_")
    assert len(body["scan"]["embedding_vector"]) == 512


def test_full_provenance_pipeline(client, monkeypatch):
    """Drive the background provenance coroutine directly through every stage.

    The HTTP layer launches ``_run_provenance_pipeline`` as a fire-and-forget
    ``asyncio.create_task``, which Starlette's ``TestClient`` (a request-scoped
    portal loop) will not reliably advance between polls. Rather than fight the
    harness, we invoke the exact same coroutine the endpoint schedules and run
    it to completion on our own loop — this exercises the real OSINT -> gate ->
    Merkle seal -> IPFS pin -> anchor path, with the network stubbed offline.
    """

    import asyncio

    from api.jobs import job_manager
    from api.routers.scan import _run_provenance_pipeline, _stage_temp_image

    img = SAMPLE.read_bytes()
    _stub_osint(monkeypatch, img)
    _stub_blockchain_and_ipfs(monkeypatch)

    # Produce a genuine scan through the real (reverted) vision pipeline.
    import api.dependencies as deps

    scan = deps.get_vision_pipeline().process_query_image(str(SAMPLE))
    assert scan is not None

    image_path = _stage_temp_image(img)
    job = job_manager.create()
    asyncio.run(
        _run_provenance_pipeline(
            job=job,
            image_path=image_path,
            image_url=None,
            scan_dict=scan.model_dump(),
        )
    )

    assert job.status.value == "completed", job.error
    stages = [e.stage for e in job.events]
    assert "merkle_seal" in stages
    assert "ipfs_pin" in stages
    assert "blockchain_anchor" in stages

    res = job.result
    assert res["merkle_root"].startswith("0x")
    assert res["ipfs_cid"]
    assert res["tx_hash"].startswith("0x")
    assert res["verified_match"] is not None
