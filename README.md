Automate SSM client Installation on Workspaces

This is a soultion designed to automate installation, registration of Workspaces as SSM clients and be able to add Tags about the workspace like Workspace ID, Assigned User, Directory ID, Region, Hostname and OS along with the AD groups the user is assigned. 

You deploy the Logon scripts to the Workspace and it calls API Endpoints to run LAmbda scripts that get SSM activation and ADD Tags to the Managed instance. 

<p align="center">
  <img src="/Docs/SSM_auto_architecture.jpg" width="550" height="450" title="Architecture Diagram">
</p>

##  Usage
The Solution contain the following
*   SAM Template that deploys the API Gateway and the Lambda Function
*   Powershell Script that is deployed to the Workspace Image that automates SSM Agent download, install and configuration
## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

