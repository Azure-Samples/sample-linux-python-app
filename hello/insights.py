"""
    Application Insights methods are defined here.
    If the Instrumentation Key Exists a telemetry client will be initialized and returned by get_telemetry_client.
    The APPINSIGHTS key should be stored in Key Vault and the application checks at runtime to get the key.
    If the key does not exist the application runs without telemetry.
"""

from applicationinsights import TelemetryClient

from hello.secrets import get_key_vault_secret


def get_instrumentation_key():
    """
        Gets an application Insight's instrumentation key from Azure Key Vault.
    """
    instrumentation_key = None

    try:
        instrumentation_key = get_key_vault_secret('APPINSIGHTSKEY')
        
    except Exception as exception:
        if instrumentation_key:
            telemetry_client = TelemetryClient(instrumentation_key)
            telemetry_client.track_exception()

    return instrumentation_key


def get_telemetry_client():
    """
        Returns a telemetry client used to communicate with application insights.
    """
    # get the telemetry key for application insights
    key = get_instrumentation_key()

    if key:
        return TelemetryClient(key)

    return None
