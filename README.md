# prometheus-jira-cloud-exporter

Forked from [https://github.com/R0quef0rt/prometheus-jira-cloud-exporter](https://github.com/R0quef0rt/prometheus-jira-cloud-exporter)

## Overview
---
While there already exist Prometheus exporter plugins for Jira Server, it is not possible to use these plugins on Jira Cloud.

As such, I have created a simple Python app that uses the [Jira library](https://github.com/pycontribs/jira) to scrape metrics from Jira Cloud's API. It uses the [Prometheus library](https://github.com/prometheus/client_python) to expose them in the correct format:

```
jira_issues{assignee="None",component="None",issueType="Bug",label="None",project="TTT",reporter="John Doe",resolution="Done",status="Done"} 1.0
jira_issues{assignee="None",component="None",issueType="Story",label="None",project="TTT",reporter="John Doe",resolution="None",status="To Do"} 2.0
jira_issues{assignee="None",component="None",issueType="Epic",label="None",project="TTT",reporter="John Doe",resolution="None",status="To Do"} 1.0
jira_issues{assignee="None",component="Active Directory",issueType="Service Request",label="Analytics and Reporting Service",project="TEST",reporter="John Doe",resolution="None",status="Waiting for support"} 1.0
jira_issues{assignee="None",component="None",issueType="Service Request",label="None",project="TEST",reporter="John Doe",resolution="None",status="Waiting for support"} 1.0
jira_issues{assignee="None",component="Active Directory",issueType="Service Request",label="HR Services",project="TEST",reporter="Example Customer",resolution="None",status="Waiting for support"} 1.0
jira_issues{assignee="John Doe",component="Active Directory",issueType="Service Request",label="Analytics and Reporting Service",project="TEST",reporter="Example Customer",resolution="Done",status="Resolved"} 1.0
jira_issues{assignee="John Doe",component="None",issueType="Task",label="None",project="GAR",reporter="John Doe",resolution="None",status="To Do"} 1.0
jira_issues{assignee="None",component="None",issueType="Task",label="None",project="GAR",reporter="John Doe",resolution="None",status="To Do"} 1.0
```

I've [created a Docker image](https://hub.docker.com/repository/docker/roquefort/prometheus-jira-cloud-exporter) you can use to quickly get started.

## How to use
---
Using this app is simple:

1. Download the project, and extract it to a folder on your computer
2. In this folder, create a ".env" file containing the following contents:
```
# The URL of your Jira Cloud instance
JIRA_URL='https://myinstance.atlassian.net'

# The username of the user authentication with Jira's API
JIRA_USER='john.doe@gmail.com'

# The API key associated with your user
JIRA_API_KEY='XXXXXXXXXXXXXXXXXX'

# The JQL query you want to use to search Jira. Leave blank to search all issues.
JQL_QUERY=''

# The interval (in seconds) to search Jira. Do not set this too low, or there is a chance
# of overloading your instance.
INTERVAL='900'

# Port to host the exporter data on (defaults to 8000 if not specified)
PORT=8000
```
3. To run this in Docker, just run the following:
```
docker-compose up --build
```
4. Navigate to http://localhost:8000 (if you specified as port 8000). Your metrics should be clearly exposed.
