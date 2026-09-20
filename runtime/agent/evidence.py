"""
Proteus Agent — Evidence Generation and Integrity (Priority 8)

Produces structured forensic evidence items with deterministic SHA-256 hashes.
Evidence is immutable once created — data is never modified post-collection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid


EVIDENCE_SCHEMA_VERSION = "1.0"


def _canonical_json(obj: Any) -> str:
    """
    Produces a deterministic JSON string for hashing.
    Uses sorted keys and compact separators for canonical form.
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str)


def compute_sha256(data: Any) -> str:
    """
    Computes a deterministic SHA-256 hash over canonical JSON of data.
    Pipeline: data → canonical JSON → UTF-8 bytes → SHA-256 → hex string
    """
    canonical = _canonical_json(data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class EvidenceItem:
    """
    Structured forensic evidence for a single operation result.
    SHA-256 is computed over the canonical JSON of 'data' at creation time.
    Data must not be modified after creation.
    """
    evidence_id: str
    job_id: str
    agent_id: str
    operation_id: str
    operation_type: str
    collected_at: str
    data: Any
    sha256: str
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    @classmethod
    def from_operation_result(
        cls,
        job_id: str,
        agent_id: str,
        operation_id: str,
        operation_type: str,
        data: Any,
    ) -> "EvidenceItem":
        """
        Creates an EvidenceItem from a raw operation result.
        Computes SHA-256 over the canonical form of data.
        """
        evidence_id = f"EVD-{uuid.uuid4().hex[:12]}"
        collected_at = datetime.now(timezone.utc).isoformat()
        sha256 = compute_sha256(data)
        return cls(
            evidence_id=evidence_id,
            job_id=job_id,
            agent_id=agent_id,
            operation_id=operation_id,
            operation_type=operation_type,
            collected_at=collected_at,
            data=data,
            sha256=sha256,
        )

    def verify(self) -> bool:
        """Verifies that the stored SHA-256 matches the current data."""
        return compute_sha256(self.data) == self.sha256.lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "collected_at": self.collected_at,
            "data": self.data,
            "sha256": self.sha256,
            "schema_version": self.schema_version,
        }


@dataclass
class EvidencePackage:
    """
    A complete evidence package for a job, including all per-operation evidence
    items and a package-level integrity hash over all results.
    """
    schema_version: str
    job_id: str
    agent_id: str
    investigation_id: str
    started_at: str
    completed_at: str
    status: str
    operations: List[Dict[str, Any]]
    evidence: List[EvidenceItem]
    package_hash: str

    @classmethod
    def build(
        cls,
        job_id: str,
        agent_id: str,
        investigation_id: str,
        started_at: str,
        completed_at: str,
        status: str,
        operation_results: List[Dict[str, Any]],
        evidence_items: List["EvidenceItem"],
    ) -> "EvidencePackage":
        """
        Builds an EvidencePackage and computes the package-level integrity hash
        over the canonical serialization of all operation results.
        """
        package_hash = compute_sha256(operation_results)
        return cls(
            schema_version="1.0",
            job_id=job_id,
            agent_id=agent_id,
            investigation_id=investigation_id,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            operations=operation_results,
            evidence=evidence_items,
            package_hash=package_hash,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "investigation_id": self.investigation_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "operations": self.operations,
            "evidence": [e.to_dict() for e in self.evidence],
            "integrity": {
                "algorithm": "SHA-256",
                "package_hash": self.package_hash,
            },
        }
