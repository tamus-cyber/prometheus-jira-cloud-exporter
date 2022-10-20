from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server
from classes.core import IssueCollector
import os
import time
from dotenv import load_dotenv


if __name__ == "__main__":
    # Import env variables
    load_dotenv()

    JQL_QUERY = os.getenv('JQL_QUERY')
    INTERVAL = int(os.getenv('INTERVAL'))
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_USER = os.getenv('JIRA_USER')
    JIRA_API_KEY = os.getenv('JIRA_API_KEY')
    PORT = int(os.getenv('PORT', default=8000))

    # Start the webserver, search Jira, and register the issue collector
    start_http_server(PORT)
    IssueCollector.construct(JQL_QUERY, JIRA_URL, JIRA_USER, JIRA_API_KEY)
    REGISTRY.register(IssueCollector())
    while True:
        time.sleep(int(INTERVAL))
