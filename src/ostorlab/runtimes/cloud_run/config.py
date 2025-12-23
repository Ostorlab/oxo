"""Configuration utilities for Cloud Run runtime."""

import os
from typing import Optional, Dict, Any


def get_gcp_config_from_env() -> Dict[str, Any]:
    """Get GCP configuration from environment variables.

    This allows users to set GCP configuration via environment variables
    instead of command line arguments.

    Returns:
        Dictionary with GCP configuration values.
    """
    config = {}

    # GCP Project ID
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        config["gcp_project_id"] = project_id

    # GCP Region
    region = os.getenv("GCP_REGION") or os.getenv("CLOUD_RUN_REGION")
    if region:
        config["gcp_region"] = region

    # Service Account
    service_account = os.getenv("GCP_SERVICE_ACCOUNT")
    if service_account:
        config["gcp_service_account"] = service_account

    return config


def validate_gcp_config(
    gcp_project_id: Optional[str],
    gcp_region: Optional[str],
) -> bool:
    """Validate GCP configuration.

    Args:
        gcp_project_id: GCP project ID.
        gcp_region: GCP region.

    Returns:
        True if configuration is valid, False otherwise.
    """
    if not gcp_project_id or not gcp_region:
        return False

    # Basic validation of project ID format
    # Project IDs must be 6-30 characters, lowercase, start with letter
    if not (6 <= len(gcp_project_id) <= 30 and gcp_project_id.islower()):
        return False

    # Basic validation of region format (e.g., us-central1)
    if not ("-" in gcp_region and len(gcp_region) >= 8):
        return False

    return True
