## **Automate SSM client Installation on Workspaces**

This is a soultion designed to automate installation & registration of Workspaces as SSM clients. Then it adds Tags to the Managed instance like Workspace ID, Assigned User, Directory ID, Region, Hostname and OS along with the AD groups the user is assigned.

With Automated Installation of SSM agent, you can use SSM tools such as Patch Managent, run Command, Automation and Distributor to Patch, deploy software and run compliance checks on your Workspace Fleet. You can also use SSM to [Monitor managed node performance](https://docs.aws.amazon.com/systems-manager/latest/userguide/fleet-monitoring.html) for troubleshooting purposes.

![alt text](Docs/SSM_auto_architecture.png)
##  Usage

The Solution contain the following
*   SAM Template that deploys the API Gateway and the Lambda Function
*   Powershell Script that is deployed to the Workspace Image that automates SSM Agent download, install and configuration
##  Steps to deploy the solution

* Clone the Repo to a machine that is configured to deploy resources in AWS.
* [Setup AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) Make sure to follow the steps on installing Docker based on the OS of your choice as we use Docker images 
* Build and deploy the SAM application 

        >sam build
        >
        >sam deploy --guided

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

