#!/bin/bash

# This script deploys and configures an Azure infrastructure for a basic web application for the collection of basic user information and payment data. 
# This script will both provision and deploy an infrastructure for supporting the basic web app. 
#         A valid Azure Subscription is Required
#         The Azure CLI module needs to be installed on the machine deploying the code.
#     This script performs several actions including: 
#         -   Creating an Azure Key Vault instance.
#         -   Creates an Azure Database for PostgreSQL instance.
#         -   Creates an Azure Webapp for Linux.
#         -   Generates self-signed SSL certificate for an application gateway (if required).
#         -   Creates an application gateway instance with WAF enabled.

function verifyPrereqs() {
    if ! [ -x "$(command -v az)" ]; then
        echo "This script requires you install Azure CLI - instructions can be found here:"
        echo "    https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        return 1 # found something missing
    fi

    if ! [ -x "$(command -v jq)" ]; then
        echo "This script requires you install 'jq' - instructions can be found here:"
        echo "    https://stedolan.github.io/jq/download/"
        return 1
    fi

    if [[ $((az account show) 2>&1) =~ "az login" ]]; then
        echo "This script requires you to be logged into Azure - here is the command:"
        echo "   az login"
        echo "(Run a cli command such as 'az account show' to confirm you are logged in.)"
        return 1
    fi

    return 0 # no issues
}

function getHash() {
    IFS='-' read -r -a array <<< "$(uuidgen)"
    echo "${array[4]}"
}

if ! verifyPrereqs; then
   if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then return; else exit; fi
fi

if [ $# -ne 2 ]; then
    echo "Two arguments are required to run this script."
    echo ""
    echo "usage: deploy-bash.sh LOCATION RESOURCE_GROUP"
    echo "    LOCATION - where to deploy (name of Azure region)"
    echo "    RG - name of Azure resource group (new or existing)"
    echo ""
    echo "example usage: ./deploy-bash.sh eastus sampleapp-dev-rg"
    echo ""
    echo "Your current Azure Subscription: " `az account show --query 'name'`
    echo "For list of region names available to pass as the LOCATION option, run this:"
    echo "    az account list-locations --query [].name"

    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then return; else exit; fi
fi


Location="$1"
ResourceGroup="$2"

echo "Location: $Location"
echo "ResourceGroup: $ResourceGroup"



# Azure KeyVault Parameters
kvName="hello-kv-$(getHash)"

# Azure Database for PostrgeSQL Parameters
dbServer="hello-pgs-$(getHash)"
dbName="hellodb"
dbRootCertPath="hello/postgres/root.crt"
dbSSLMode="verify-ca"
dbPort=5432

# App Service Parameters
appServicePlanName="hello-aps-$(getHash)"
appName="hello-asl-$(getHash)"
containerName="mcr.microsoft.com/samples/basic-linux-app"


# Application Gateway Parameters
gwName="hello-gw-$(getHash)"
gwProbe="gw-probe"
gwProbePath="/hello"

vnetName="hello-vnet-$(getHash)"
vnetAddressPrefix="10.0.0.0/16"
gatewayAddressPrefix="10.0.1.0/24"
publicIpName="hello-pip-$(getHash)"
gwSubnet="gw-subnet"

filePath="appgwcert.pfx"
tempPem="appgwcert.pem"
certPath="gateway.pfx"
certName="gatewaySSLCert"


# Registering the Azure Key Vault resource provider for Azure CLI
az provider register -n Microsoft.KeyVault

# Create a resource group for the Azure Key Vault instance
echo "Creating Azure Resource Group: $ResourceGroup"
az group create --name $ResourceGroup \
    --location $Location \
    --verbose


# Create the Azure Key Vault instance
echo "Creating Azure Key Vault instance: $kvName"
az keyvault create --name $kvName \
    --resource-group $ResourceGroup \
    --location $Location \
    --verbose


# Generate usernames and passwords using system functions and environment variables
pgUsername=$(echo "$USER$(openssl rand -base64 10)" | tr -cd '[:alnum:]')

pgPassword=$(openssl rand -base64 30) # 30 random bytes x 4/3 (growth from base64 encoding) = 40 char password
pgPassword=$(echo $pgPassword | tr -cd '[:alnum:]') # more convenient characters, but no less random

# Set the username secret in the Azure Key Vault instance
echo "Setting PostgreSQL username in KeyVault"
az keyvault secret set --vault-name $kvName \
    --name PGUSERNAME \
    --value $pgUsername \
    --verbose


# Set the password secret in the Azure Key Vault instance
echo "Setting PostgreSQL password in KeyVault"
az keyvault secret set --vault-name $kvName \
    --name PGPASSWORD \
    --value $pgPassword \
    --verbose



# POSTGRESQL DEPLOYMENT

# Retrieve username and password from Azure Key Vault instance
echo "Retrieving PostgreSQL username and password from KeyVault"
pgUsername=$(az keyvault secret show --name PGUSERNAME --vault-name $kvName --query value) 
pgPassword=$(az keyvault secret show --name PGPASSWORD --vault-name $kvName --query value)


# Strip quotes from the credentials
pgUsername=$(echo $pgUsername | tr -d '"')
pgPassword=$(echo $pgPassword | tr -d '"')



# Create an Azure Database for PostgreSQL server
echo "Creating the PostreSQL server: $dbServer"
az  postgres server create -l $Location \
    --resource-group $ResourceGroup \
    --name $dbServer \
    --admin-user $pgUsername \
    --admin-password $pgPassword \
    --sku-name B_Gen5_1 \
    --verbose

# Create a database in our server instance created above
echo "Creating the PostgreSQL database: $dbName"
az postgres db create --resource-group $ResourceGroup \
    --server-name $dbServer \
    --name $dbName \
    --verbose

echo "Generating the PostgreSQL connection string"
# Retrieve the database information above
db=$(az postgres server show --resource-group $ResourceGroup \
        --name $dbServer)

# Get the Fully Qualified Domain Name (FQDN) of the database to use in
# the databse connection strings to be store in Azure Key Vault
fullyQualifiedDomainName=$(echo $db | jq '.fullyQualifiedDomainName')
fullyQualifiedDomainName=$(echo $fullyQualifiedDomainName | tr -d '"')

PGCONNECTIONSTRING="postgresql+psycopg2://$pgUsername:$pgPassword@$fullyQualifiedDomainName:$dbPort/$dbName?sslmode=$dbSSLMode&sslrootcert=$dbRootCertPath"

# Set the database connection string above into Azure Key Vault
echo "Setting the PostgreSQL connection string into KeyVault"
az keyvault secret set --vault-name $kvName \
    --name PGCONNECTIONSTRING \
    --value $PGCONNECTIONSTRING \
    --verbose


# APP SERVICE DEPLOYMENT

# Retrieve the Azure Key Vault instance's URI to be used by the web app in accessing the resources
echo "Retrieving the Azure Key Vault URL"
kvURI=$(az keyvault show --name $kvName --query properties.vaultUri)
kvURI=$(echo $kvURI | tr -d '"')


# Create the app service plan, using --linux as we're running containers on Web App for Linux
echo "Creating App Service Plan: $appName"
az appservice plan create --name $appServicePlanName \
    --resource-group $ResourceGroup \
    --location $Location \
    --number-of-workers 1 \
    --sku B1 \
    --is-linux \
    --verbose

# Create the Web App
echo "Creating Azure Web App for Linux: $appName"
az webapp create --name $appName \
    --resource-group $ResourceGroup \
    --plan $appServicePlanName \
    --deployment-container-image-name $containerName \
    --verbose

# Assign a systemm assigned identity
# This creates a Service Principal to be used for MSI allowing access to Key Vault Secrets without using auth keys/tokens
echo "Assigning Service Principal Identity to webapp: $appName"
az webapp identity assign --name $appName \
    --resource-group $ResourceGroup \
    --verbose 

# Configure logging for the docker container on app service
echo "Configuring logging for the web app: $appName"
az webapp log config --name $appName \
    --resource-group $ResourceGroup \
    --application-logging true \
    --detailed-error-messages true \
    --docker-container-logging filesystem \
    --verbose


# Set app configuration settings to be set in the container's environment variables
echo "Setting app setings for our web app: $appName"
az webapp config appsettings set --name $appName \
    --resource-group $ResourceGroup \
    --settings WEBSITE_TIME_ZONE=$timezone KEY_VAULT_URI=$kvURI \
    --verbose

# Stop the web app to allow us to enable us to first allow the created MSI Service Principals access to the Key Vault instance
az webapp stop --name $appName \
    --resource-group $ResourceGroup \
    --verbose


# Get all the outbound IP's the app service instance may use
echo "Adding outbound Azure App Service IP's to the PostgreSQL database firewall."
outboundIps=$(az webapp show --resource-group $ResourceGroup \
    --name $appName \
    --query outboundIpAddresses \
    --output tsv | tr ',' '\n')


IFS=',' read -r -a outboundIpsArray <<< $outboundIps
outboundIpsArrayLength=${#outboundIpsArray[@]}


# Loop over all the outbound IP addresses and whitelist them in the PostgreSQL Firewall
i=0 # counter so firewall rule entries have distinct names
for ip in $outboundIps
do
    ((i++))
    echo "Adding IP Rule ${i} for ${ip}-${ip} on PostgreSQL for App Service"

    az postgres server firewall-rule create --name "OUTBOUND_IP_RULE_$i" \
        --resource-group $ResourceGroup \
        --server-name $dbServer \
        --start-ip-address $ip \
        --end-ip-address $ip \
        --verbose
done


# APP GATEWAY DEPLOYMENT

echo "Retrieving the app service hostName for app $appName"
appHostName=$(az webapp show --resource-group $ResourceGroup --name $appName --query defaultHostName)
appHostName=$(echo $appHostName | tr -d '"')

# Uncomment this line to scaffold a new domain, for now the gateway.json provides a configuration for the self signed certificate
# There is a default policy.json file in the scripts folder that mocks provides stud info for the self-signed certificate
# Modify the policy.json or scaffold a new one that matches your domains and contact information
# az keyvault certificate get-default-policy --scaffold > policy.json

# Create a Self-Signed Certificate from the Azure Policy
echo "Creating a self-signed azure certificate: $certName"
az keyvault certificate create --vault-name $kvName \
    --name $certName \
    --policy @policy.json \
    --verbose

# Download the certificate created above in base64
echo "Downloading the self-signed certificate created"
az keyvault secret download --file $filePath \
    --encoding base64 \
    --name $certName \
    --vault-name $kvName \
    --verbose

# Create a random password for the certificate
certPassword=$(openssl rand -base64 12) # 12 random bytes x 4/3 (growth from base64 encoding) = 16 char password
certPassword=$(echo $certPassword | tr -cd '[:alnum:]') # more convenient characters, but no less random

# Set the password in Azure Key Vault
echo "Setting the certificate password into Azure Key Vault"
az keyvault secret set --vault-name $kvName \
    --name CERTPASSWORD \
    --value $certPassword \
    --verbose

# Export the certificate with the password
openssl pkcs12 -in $filePath -out $tempPem -nodes -passin pass:
openssl pkcs12 -export -out $certPath -in $tempPem -passin pass: -passout pass:$certPassword


# Create a vitual network required by the gateway
echo "Creating the Azure Virtual Network: $vnetName"
az network vnet create --name $vnetName \
    --resource-group $ResourceGroup \
    --location $Location \
    --address-prefix $vnetAddressPrefix \
    --verbose

# Add a subnet to the virtual network above
echo "Creating the Subnet: $gwSubnet"
az network vnet subnet create --name $gwSubnet \
    --resource-group $ResourceGroup \
    --vnet-name $vnetName \
    --address-prefix $gatewayAddressPrefix \
    --verbose

# Create a public IP Address that will be used by clients to access the application gateway
echo "Creating the Public IP Address: $publicIpName"
az network public-ip create --resource-group $ResourceGroup \
    --name $publicIpName \
    --verbose

# Create the application gateway
echo "Creating the Application Gateway: $gwName"
az network application-gateway create \
    --name $gwName \
    --resource-group $ResourceGroup \
    --location $Location \
    --vnet-name $vnetName \
    --subnet $gwSubnet \
    --public-ip-address $publicIpName \
    --http-settings-cookie-based-affinity Disabled \
    --frontend-port 443 \
    --http-settings-protocol Https \
    --http-settings-port 443 \
    --capacity 2 \
    --sku WAF_Medium \
    --cert-file $certPath \
    --cert-password $certPassword \
    --verbose

# Enable the firewall with OWASP ruleset 3.0 on the application gateway
echo "Creating the Application Gateway WAF Configuration"
az network application-gateway waf-config set \
    --enabled true \
    --gateway-name $gwName \
    --resource-group $ResourceGroup \
    --firewall-mode Detection \
    --rule-set-version 3.0 \
    --verbose

# Retrieve the name of the http settings that will be updated below.
gwHTTPSettings=$(az network application-gateway http-settings list --resource-group $ResourceGroup --gateway-name $gwName)
gwHTTPSettingsName=$(echo $gwHTTPSettings | jq ".[0] | .name" | tr -d '"')

# Retrieve the name of the backend address pool that will be updated below.
gwAddressPool=$(az network application-gateway address-pool list --resource-group $ResourceGroup --gateway-name $gwName)
gwAddressPoolName=$(echo $gwAddressPool | jq ".[0] | .name" | tr -d '"')

# Update the backend pool with the app service hostname
echo "Updating the Azure Application Gateway backend pool host name: $appHostName"
az network application-gateway address-pool update --name $gwAddressPoolName \
    --resource-group $ResourceGroup \
    --gateway-name $gwName \
    --servers $appHostName \
    --verbose

# Create a probe that will check for the backend pool's availability.
echo "Updating the Azure Application Gateway Probe: $gwProbe"
az network application-gateway probe create --gateway-name $gwName \
    --name $gwProbe \
    --resource-group $ResourceGroup \
    --protocol Https \
    --path $gwProbePath \
    --host-name-from-http-settings true \
    --verbose

# Update the app to user https and to pick the hostname from the backend settings.
echo "Deploying the updated application gateway"
az network application-gateway http-settings update --gateway-name $gwName \
    --resource-group $ResourceGroup \
    --name $gwHTTPSettingsName \
    --connection-draining-timeout 0 \
    --enable-probe true \
    --host-name-from-backend-pool true \
    --probe $gwProbe \
    --protocol Https \
    --port 443 \
    --verbose

# FIN
