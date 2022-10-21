from prometheus_client.core import GaugeMetricFamily, REGISTRY
from jira import JIRA, JIRAError
import time
import json
from loguru import logger


class IssueCollector:

    jira = None
    custom_fields = None
    custom_fields_str = None
    block_num = 0
    prom_output = {}

    @classmethod
    def search(self, jql):

        # Search Jira API
        block_size = 100
        result = self.jira.search_issues(
            jql,
            startAt=self.block_num * block_size,
            maxResults=block_size,
            fields=f"project, summary, components, labels, status, issuetype, resolution, created, resolutiondate, reporter, assignee, status, description, {self.custom_fields_str}",
        )
        return result

    @classmethod
    def construct(self, jql, url, user, apikey):
        self.jira = JIRA(basic_auth=(user, apikey), options={"server": url})
        # Get custom fields from custom_field_map.json if it exists
        try:
            with open("custom_field_map.json", "r") as f:
                self.custom_fields = json.load(f)
                logger.debug(f"Custom fields: {self.custom_fields}")
                self.custom_fields_str = ", ".join(self.custom_fields.keys())
        except FileNotFoundError:
            self.custom_fields = {}
            self.custom_fields_str = ""
        try:

            prom_labels = []
            result = IssueCollector.search(jql)

            # Loop over the JQL results
            while bool(result):
                for issue in result:
                    # Assign Jira attributes to variables
                    project = str(issue.fields.project)
                    summary = str(issue.fields.summary)
                    created = str(issue.fields.created)
                    resolutiondate = str(issue.fields.resolutiondate)
                    assignee = str(issue.fields.assignee)
                    issue_type = str(issue.fields.issuetype)
                    status = str(issue.fields.status)
                    resolution = str(issue.fields.resolution)
                    reporter = str(issue.fields.reporter)
                    components = issue.fields.components
                    labels = issue.fields.labels
                    root_cause = str(issue.fields.customfield_10320)

                    # Get custom fields
                    custom_fields = {}
                    for key, value in self.custom_fields.items():
                        custom_fields[value] = str(issue.fields.__dict__[key])

                    # Construct the list of labels from attributes
                    prom_label = [
                        project,
                        summary,
                        created,
                        resolutiondate,
                        assignee,
                        issue_type,
                        status,
                        resolution,
                        reporter,
                    ]

                    # Add custom fields to the list of labels
                    for key, value in custom_fields.items():
                        prom_label.append(value)

                    if components:
                        for component in components:
                            prom_label.append(str(component))
                    else:
                        prom_label.append("None")
                    if labels:
                        for label in labels:
                            prom_label.append(str(label))
                    else:
                        prom_label.append("None")
                    prom_labels.append(prom_label)
                # Increment the results via pagination
                self.block_num += 1
                time.sleep(2)
                result = IssueCollector.search(jql)
            self.jira.close()

            # Convert nested lists into a list of tuples, so that we may hash and count duplicates
            for li in prom_labels:
                self.prom_output.setdefault(tuple(li), list()).append(1)
            for k, v in self.prom_output.items():
                self.prom_output[k] = sum(v)
            return self.prom_output
        except (JIRAError, AttributeError):
            logger.exception("Error while searching Jira")
            self.jira.close()

    @classmethod
    def collect(self):
        # Set up the Issues Prometheus gauge
        labels=[
                "project",
                "summary",
                "created",
                "resolutiondate",
                "assignee",
                "issue_type",
                "status",
                "resolution",
                "reporter",
                "component",
                "label",
            ]
        # Add custom fields to the list of labels
        for key, value in self.custom_fields.items():
            # Insert before component and label
            labels.insert(-2, value)
        issues_gauge = GaugeMetricFamily(
            "jira_issues",
            "Jira issues",
            labels=labels,
        )

        for labels, value in self.prom_output.items():
            issues_gauge.add_metric(labels, value)
        yield issues_gauge
