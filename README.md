# Sample Linux Python App

This repository contains source code for a Python Application built on Azure WebApp for Linux containers that contains the following.

* A Docker file - `Dockerfile`
* Python web app source code (Flask) - `src`
* Deployment scripts - `scripts`
* An init file for the Docker container - `init.sh`
* A migrations folder for Flask database migrations - `migrations`

## Getting Started

### Prerequisites

1. Install a code editor to modify and view the application code. For the sample app, [Visual Studio Code](https://code.visualstudio.com/) was used.
2. Install the [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli?view=azure-cli-latest&viewFallbackFrom=azure-cli-latest,) on your development machine.
3. Install [Git](https://git-scm.com/) on your system. Git is used to clone the source code locally.
4. Install [jq](https://stedolan.github.io/jq/) if you are on a Linux based system, jq being a tool for querying JSON in a user friendly way.

### Deploying

Change directory into the scripts folder `cd scripts`

1. If you are on powershell run the `deploy-powershell.ps1` file by typing `./deploy-powershell.ps1 <REGION> <RESOURCE_GROUP_NAME>` replacing the region and resource group name with suitable Azure regions and a name for the resource group
2. If you are on linux run the `deploy-bash.sh` file by typing `/deploy-bash.sh <REGION> <RESOURCE_GROUP_NAME>`, you may have to make the file executable by typing `chmod +x deploy-bash.sh`
3. After the resources have been deployed, read the documentation contained here to configure the resources in order to make the app run, without the configuration described in the documentation the application will not run

---
**NOTE**

After deployment this application needs to be configured as outlined in the documentation here [App Documentation](https://docs.microsoft.com/azure/security/develop/secure-web-app),
otherwise the components will not work correctly without specifying the necessary steps

---

## Resources

1. [Security Development Lifecycle](https://www.microsoft.com/en-us/securityengineering/sdl)
2. [Security Patterns](https://docs.microsoft.com/en-us/azure/security/security-best-practices-and-patterns)
3. [Python On Azure](https://azure.microsoft.com/en-us/develop/python/)
