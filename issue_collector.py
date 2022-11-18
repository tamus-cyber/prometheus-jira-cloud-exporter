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
            startAt=0,
            maxResults=False,
            fields=f"project, summary, components, labels, status, issuetype, resolution, created, resolutiondate, reporter, updated, assignee, status, {self.custom_fields_str}",
        )
        logger.debug("Response length: " + str(len(result)))
        return result

    @classmethod
    def construct(self, jql, url, user, apikey, async_workers=10):
        # DEBUG: Log amount of time this takes
        start_time = time.time()
        self.jira = JIRA(basic_auth=(user, apikey), options={"server": url}, async_=True, async_workers=async_workers)
        # Get custom fields from custom_field_map.json if it exists
        try:
            with open("custom_field_map.json", "r") as f:
                self.custom_fields = json.load(f)
                # If any keys have a ., only keep the part before the .
                parsed_custom_fields = {
                    k.split(".")[0]: v for k, v in self.custom_fields.items()
                }
                self.custom_fields_str = ",".join(parsed_custom_fields.keys())
        except FileNotFoundError:
            self.custom_fields = {}
            self.custom_fields_str = ""
        try:
            prom_labels = []
            self.block_num = 0
            result = IssueCollector.search(jql)

            # Loop over the JQL results
            for issue in result:
                # Write to JSON
                with open("test.json", "w") as f:
                    json.dump(issue.raw, f, indent=4)
                # Assign Jira attributes to variables
                project = str(issue.fields.project)
                project_name = str(issue.fields.project.name)
                issue_key = str(issue.key)
                summary = str(issue.fields.summary)
                created = str(issue.fields.created)
                resolutiondate = str(issue.fields.resolutiondate)
                assignee = str(issue.fields.assignee)
                issue_type = str(issue.fields.issuetype)
                status = str(issue.fields.status)
                reporter = str(issue.fields.reporter)
                resolution = str(issue.fields.resolution)
                updated = str(issue.fields.updated)
                components = issue.fields.components
                labels = issue.fields.labels

                # Get custom fields
                custom_fields = {}
                for key, value in self.custom_fields.items():
                    # If the key has a . in it, it's a nested field, use recursion to get the value
                    if "." in key:
                        custom_fields[value] = self.get_nested_field(issue.raw['fields'], key)
                    else:
                        custom_fields[value] = str(issue.fields.__dict__[key])

                # Construct the list of labels from attributes
                prom_label = [
                    project,
                    project_name,
                    issue_key,
                    summary,
                    created,
                    resolutiondate,
                    assignee,
                    issue_type,
                    status,
                    resolution,
                    updated,
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
            self.jira.close()
            # DEBUG: Log amount of time this takes
            end_time = time.time()
            logger.debug(f"Time to construct: {end_time - start_time}")

            # Convert nested lists into a list of tuples, so that we may hash and count duplicates
            # Reset prom_output
            self.prom_output = {}
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
                "project_name",
                "issue_key",
                "summary",
                "created",
                "resolutiondate",
                "assignee",
                "issue_type",
                "status",
                "resolution",
                "updated",
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

    
    @classmethod
    # Credit: https://stackoverflow.com/a/67225625
    def walktree(self, tree, at=lambda node: not isinstance(node, dict), prefix=(), 
                flattennode=lambda node:isinstance(node, (list, tuple, set))):
        """
        Traverse a tree, and return a iterator of the paths from the root nodes to the leaf nodes.
        tree: like '{'a':{'b':1,'c':2}}'
        at: a bool function or a int indicates levels num to go down. walktree(tree, at=1) equivalent to tree.items()
        flattennode: a bool function to decide whether to iterate at node value
        """
        if isinstance(at, int):
            isleaf_ = at == 0
            isleaf = lambda v: isleaf_
            at = at - 1
        else:
            isleaf = at
        if isleaf(tree):
            if not flattennode(tree):
                yield (*prefix, tree)
            else:
                for v in tree:
                    yield from self.walktree(v, at, prefix, flattennode=flattennode)
        else:
            for k,v in tree.items():
                yield from self.walktree(v, at, (*prefix, k), flattennode=flattennode)   


    @classmethod
    def get_nested_field(self, issue, key):
        """Take a nested field and return the value
        
        Example: key = "customfield_10000.value[0].value"
        Example: issue = {"customfield_10000": {"value": [{"value": "foo"}]}}

        Args:
            issue: The issue to get the field from
            key: The key to get the value from

        Returns:
            value: The value of the field
        """
        # Split the key into a list
        key_list = key.split(".")
        # Get the first key
        first_key = key_list.pop(0)
        # If the key is a *, then we traverse every key in the dict to find the value after the *
        if first_key == "*":
            # Get the value after the *
            value_key = key_list.pop(0)
            # Walk the tree and unpack into lists of all possible leaf nodes
            unpacked = list(self.walktree(issue))
            # Check each leaf node to see if it matches the value key
            for item in unpacked:
                # If the value key matches, return the value
                # Example: ('completedCycles', 'breached', True) when looking for "customfield_10600.*.breached"
                if item[-2] == value_key:
                    return str(item[-1])
            
        value = issue[first_key]
        # If there are more keys, recurse
        if key_list:
            return self.get_nested_field(value, ".".join(key_list))
        else:
            return str(value)
