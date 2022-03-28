Automate SSM client Installation on Workspaces

This is a soultion designed to automate installation, registration of Workspaces as SSM clients and be able to add Tags about the workspace like Workspace ID, Assigned User, Directory ID, Region, Hostname and OS along with the AD groups the user is assigned. 

You deploy the Logon scripts to the Workspace and it calls API Endpoints to run LAmbda scripts that get SSM activation and ADD Tags to the Managed instance. 

![alt text](aws-samples/workspaces-ssm-install/tree/main/Docs/SSM_auto_architecture.png)
##  Usage
The Solution contain the following
*   SAM Template that deploys the API Gateway and the Lambda Function
*   Powershell Script that is deployed to the Workspace Image that automates SSM Agent download, install and configuration
##  Steps to deploy the solution
* Clone the Repo to a machine that is configured to deploy resources in AWS.
* checkout its <a href="/aws-samples/aws-lambda-adapter/blob/main/docs/design.md">design</a> and <a href="/aws-samples/aws-lambda-adapter/blob/main/docs/development.md">development</a> documents.</p>

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

