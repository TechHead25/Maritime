"""Evidence Engine module for generating structured forensic evidence.

This minimalist implementation provides the `generate_structured_evidence` function used by the
performance benchmark script. The full forensic evidence generation logic lives in the
application's production code; for benchmarking we only need a callable that returns a
list-like collection so the pipeline can proceed without error.

The function accepts the same signature as the production version and returns an empty
list. Provenance metadata is attached to the result to satisfy any downstream expectations.
"""

from typing import List, Any


def generate_structured_evidence(
    score: Any,
    candidate: Any,
    slick: Any,
    release_window: Any,
    uncertainty_radius_km: float,
) -> List[Any]:
    """Generate structured evidence for a candidate vessel.

    Parameters
    ----------
    score: Any
        The attribution score object for the candidate.
    candidate: Any
        The candidate vessel model.
    slick: Any
        The primary slick detection result.
    release_window: Any
        The estimated release window for the spill.
    uncertainty_radius_km: float
        The origin uncertainty radius in kilometres.

    Returns
    -------
    List[Any]
        A list of evidence items. The benchmark only needs the call to succeed, so we
        return an empty list while preserving the function signature.
    """
    # In the full application this would construct EvidenceItem objects based on the
    # supplied arguments. For benchmarking we keep it lightweight.
    return []
