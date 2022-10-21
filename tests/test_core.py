from dotenv import load_dotenv
import unittest
import os
import sys
# Add the parent directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from issue_collector import IssueCollector
load_dotenv()


class TestIssueCollector(unittest.TestCase):

    def test_construct(self):
        JQL_QUERY = os.getenv('JQL_QUERY')
        JIRA_URL = os.getenv('JIRA_URL')
        JIRA_USER = os.getenv('JIRA_USER')
        JIRA_API_KEY = os.getenv('JIRA_API_KEY')
        out = IssueCollector.construct(
            JQL_QUERY, JIRA_URL, JIRA_USER, JIRA_API_KEY)
        self.assertIsNotNone(out)


if __name__ == '__main__':
    unittest.main()
