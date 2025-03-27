# Deploying a Wasp App to Shared Hosting with Arc

This example demonstrates how to deploy a Wasp application to a shared hosting environment using Arc.

## Prerequisites

- Python 3.10+
- Wasp CLI installed
- SSH access to your shared hosting
- Arc installed

## Step 1: Authenticate with your shared hosting

First, you need to authenticate with your shared hosting provider. You'll need to provide the following credentials:

```python
from arc.credentials import CredentialsManager

# Initialize credentials manager
credentials_manager = CredentialsManager("~/.arc/credentials")

# Store credentials
credentials_manager.store_credentials("shared_hosting", {
    "host": "your-server.example.com",
    "username": "your-ssh-username",
    "password": "your-ssh-password",  # Optional if using key-based authentication
    "key_file": "~/.ssh/id_rsa"  # Optional path to your private key
})
```

## Step 2: Create a deployment configuration

Create a JSON file named `deployment.json` with your deployment configuration:

```json
{
  "framework": "wasp",
  "provider": "shared_hosting",
  "app_name": "my-wasp-app",
  "config": {
    "include_auth": true,
    "database_type": "postgresql",
    "ssh_directory": "/home/your-username/public_html/my-wasp-app",
    "setup_database": true,
    "database_name": "my_wasp_app_db",
    "database_user": "db_user"
  }
}
```

## Step 3: Run deployment with Arc

```python
import asyncio
from arc.server import ArcServer

async def deploy():
    # Initialize Arc server
    server = ArcServer(debug=True)
    
    # Deploy the framework
    result = await server.deploy_framework(
        framework="wasp",
        provider="shared_hosting",
        app_name="my-wasp-app",
        config={
            "include_auth": True,
            "database_type": "postgresql",
            "ssh_directory": "/home/your-username/public_html/my-wasp-app",
            "setup_database": True,
            "database_name": "my_wasp_app_db",
            "database_user": "db_user"
        }
    )
    
    print(result)

# Run the deployment
asyncio.run(deploy())
```

## Step 4: Verify deployment

After deployment, you can verify that your application is running correctly:

1. Visit your website at: `http://your-server.example.com/my-wasp-app`
2. Check that all routes are working
3. Verify database connections

## Troubleshooting

If you encounter issues during deployment, you can use the `troubleshoot_deployment` tool:

```python
async def troubleshoot():
    server = ArcServer(debug=True)
    
    # Get error logs from your shared hosting
    error_logs = "... paste error logs here ..."
    
    # Analyze logs and get suggestions
    suggestions = await server.troubleshoot_deployment(
        framework="wasp",
        provider="shared_hosting",
        error_logs=error_logs
    )
    
    print(suggestions)

# Run troubleshooting
asyncio.run(troubleshoot())
```

## Example with Claude Desktop

When using Claude Desktop with the Arc MCP server, you can have a natural language conversation to deploy your application. Here's an example dialogue:

```
You: I need to deploy my Wasp application to my shared hosting provider. Can you help me with that?

Claude: I'd be happy to help you deploy your Wasp application to shared hosting. Let's go through the process step by step.

First, I'll need some information:
1. What's the name of your Wasp application?
2. Do you have SSH access to your shared hosting?
3. What's the SSH hostname, username, and either password or key file?
4. Where on the server do you want to deploy the application?
5. Does your application require a database, and if so, what type?

You: My app is called "task-manager". I have SSH access with username "myuser" on host "example.com" using a key file. I want to deploy to "/home/myuser/public_html/tasks" and I need a PostgreSQL database.

Claude: Great! Let me help you deploy your "task-manager" app to your shared hosting.

First, I'll need to store your credentials securely. I'll use the Arc credentials manager to do this:

[Claude uses the authenticate_provider tool to securely store credentials]

Now, I'll analyze the requirements for deploying a Wasp application to shared hosting:

[Claude uses the analyze_requirements tool to check compatibility]

Everything looks compatible. Let's proceed with the deployment:

[Claude uses the deploy_framework tool to deploy the application]

Your application has been successfully deployed! You can access it at http://example.com/tasks

Would you like me to help you troubleshoot any issues or explain how to make updates to your deployed application?
```

This example shows how Arc makes deployment accessible through natural language interaction with Claude.
