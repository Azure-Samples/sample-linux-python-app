"""
    Secrets is a module that interacts with KeyVault.
    The KeyVault URI is stored in the application settings
    when the deployment is run.
"""

import os

from azure.keyvault import KeyVaultClient
from msrestazure.azure_active_directory import MSIAuthentication


def get_auth_credentials():
    """
        Get an instance of the MSI authentication for Key Vault resources.
    """
    return MSIAuthentication(
        resource="https://vault.azure.net"
    )


def get_key_vault_secret(key, version="") -> str:
    """
        Gets a secret from Key Vault given the secrets name.
    """
    # get MSI credentials for authenticating against Key Vault
    credentials = get_auth_credentials()

    client = KeyVaultClient(
        credentials
    )

    # get Key Vault URL from the Application Settings
    key_vault_uri = os.environ.get("KEY_VAULT_URI")

    # retrieve a secret that matches the corresponding key value
    key_bundle = client.get_secret(key_vault_uri, key, version)

    return key_bundle.value
