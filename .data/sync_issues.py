import os
import time
from functools import lru_cache

from github import Github
from github.GithubException import UnknownObjectException, GithubException

# Issues list. Each issue is in the format:
# {
#   "id": 1,  # corresponds to the issue 001
#   "parent": 5,  # corresponds to the issue 005 => issue is duplicate of 005
#   "closed": True,  # True for a closed, unlabeled or low/info issue
#   "auditor": "rcstanciu",
#   "severity": "H",  # or None if the issue is unlabeled, closed or low/info
#   "title": "Issue title",
#   "body": "Issue body",
#   "has_duplicates": True,
# }
issues = {}


def process_directory(repo, path):
    global issues

    repo_items = [
        x
        for x in repo.get_contents(path)
        if x.name
        not in [".data", ".github", "README.md", "Audit_Report.pdf"]
    ]
    for item in repo_items:
        print("Reading file %s" % item.name)
        if item.name in ["unlabeled", "low-info", "closed"]:
            process_directory(repo, item.path)
            continue

        parent = None
        closed = any(x in path for x in ["unlabeled", "low-info", "closed"])
        files = []
        dir_issues_ids = []
        severity = None
        if item.type == "dir":
            # If it's a directory, we have some duplicate issues
            files = list(repo.get_contents(item.path))
            try:
                if not closed:
                    severity = item.name.split("-")[1]
            except Exception:
                pass
        else:
            # If it's a file, there is a solo issue
            files = [item]

        for file in files:
            if "report" in file.name:
                issue_id = int(file.name.replace("-report.md", ""))
                parent = issue_id
            else:
                issue_id = int(file.name.replace(".md", ""))

            body = file.decoded_content.decode("utf-8")
            auditor = body.split("\n")[0]
            title = auditor + " - " + body.split("\n")[4].split("# ")[1]
            if not severity:
                severity = body.split("\n")[2][0].upper()
            issues[issue_id] = {
                "id": issue_id,
                "parent": None,
                "severity": severity,
                "body": body,
                "closed": closed,
                "auditor": auditor,
                "title": title,
                "has_duplicates": False,
            }
            dir_issues_ids.append(issue_id)

        # Set the parent field for all duplicates in this directory
        if len(files) > 1 and parent is None:
            raise Exception(
                "Issue %s does not have a primary file (-report.md)." % item.path
            )

        if parent:
            for issue_id in dir_issues_ids:
                if issue_id != parent:
                    issues[parent]["has_duplicates"] = True
                    issues[issue_id]["parent"] = parent
                    issues[issue_id]["closed"] = True


@lru_cache(maxsize=1024)
def get_github_issue(repo, issue_id):
    print("Fetching issue #%s" % issue_id)
    return repo.get_issue(issue_id)


def main():
    global issues

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_number = int(os.environ.get("GITHUB_RUN_NUMBER"))

    github = Github(token)
    repo = github.get_repo(repo)

    process_directory(repo, "")
    # Sort them by ID so we match the order
    # in which GitHub Issues created
    issues = dict(sorted(issues.items(), key=lambda item: item[1]["id"]))

    labels = [
        {"name": "High", "color": "B60205"},
        {"name": "Medium", "color": "D93F0B"},
        {"name": "Low", "color": "FBCA04"},
        {"name": "Informational", "color": "0E8A16"},
        {"name": "Has Duplicates", "color": "D4C5F9"},
        {"name": "Duplicate", "color": "EDEDED"},
        {"name": "Sponsor Confirmed", "color": "1D76DB"},
        {"name": "Sponsor Disputed", "color": "0E8A16"},
        {"name": "Disagree With Severity", "color": "5319E7"},
        {"name": "Disagree With (non-)Duplication", "color": "F9D0C4"},
        {"name": "Will Fix", "color": "BFDADC"},
    ]
    label_names = [x["name"] for x in labels]

    # Create the labels if it's the first time this action is run
    if run_number == 1:
        print("Creating issue labels")
        existing_labels = list(repo.get_labels())
        existing_label_names = [x.name for x in existing_labels]
        for label in existing_labels:
            if label.name not in label_names:
                label.delete()

        for label in labels:
            if label["name"] not in existing_label_names:
                repo.create_label(**label)
    else:
        print("Skipping creating labels.")

    # Sync issues
    for issue_id, issue in issues.items():
        print("Issue #%s" % issue_id)

        issue_labels = []
        if issue["severity"] == "H":
            issue_labels = ["High"]
        elif issue["severity"] == "M":
            issue_labels = ["Medium"]
        elif issue["severity"] == "L":
            issue_labels = ["Low"]
        elif issue["severity"] == "I":
            issue_labels = ["Informational"]

        if issue["has_duplicates"]:
            issue_labels.append("Has Duplicates")
        elif issue["parent"]:
            issue_labels.append("Duplicate")

        # Try creating/updating the issue until a success path is hit
        must_sleep = False
        while True:
            try:
                # Fetch existing issue
                gh_issue = get_github_issue(repo, issue_id)

                # We persist all labels except High/Medium/Has Duplicates/Duplicate
                existing_labels = [x.name for x in gh_issue.labels]
                new_labels = existing_labels.copy()
                if "High" in existing_labels:
                    new_labels.remove("High")
                if "Medium" in existing_labels:
                    new_labels.remove("Medium")
                if "Low" in existing_labels:
                    new_labels.remove("Low")
                if "Informational" in existing_labels:
                    new_labels.remove("Informational")
                if "Has Duplicates" in existing_labels:
                    new_labels.remove("Has Duplicates")
                if "Duplicate" in existing_labels:
                    new_labels.remove("Duplicate")
                new_labels = issue_labels + new_labels

                must_update = False
                if existing_labels != new_labels:
                    must_update = True
                    print(
                        "\tLabels differ. Old: %s New: %s"
                        % (existing_labels, new_labels)
                    )

                if gh_issue.title != issue["title"]:
                    must_update = True
                    print(
                        "\tTitles differ: Old: %s New: %s"
                        % (gh_issue.title, issue["title"])
                    )

                expected_body = issue["body"] if not issue["parent"] else issue["body"] + f"\n\nDuplicate of #{issue['parent']}\n"
                if expected_body != gh_issue.body:
                    must_update = True
                    print("\tBodies differ. See the issue edit history for the diff.")

                if must_update:
                    print("\tIssue needs to be updated.")
                    gh_issue.edit(
                        title=issue["title"],
                        body=issue["body"],
                        state="closed" if issue["closed"] else "open",
                        labels=new_labels,
                    )
                    # Exit the inifite loop and sleep
                    must_sleep = True
                    break
                else:
                    print("\tIssue does not need to be updated.")
                    # Exit the infinite loop and don't sleep
                    # since we did not make any edits
                    break
            except UnknownObjectException:
                print("\tCreating issue")
                # Create issue - 1 API call
                gh_issue = repo.create_issue(
                    issue["title"], body=issue["body"], labels=issue_labels
                )
                if issue["closed"]:
                    gh_issue.edit(state="closed")

                # Exit the infinite loop and sleep
                must_sleep = True
                break
            except GithubException as e:
                print(e)
                # Sleep for 5 minutes (in case secondary limits have been hit)
                # Don't exit the inifite loop and try again
                time.sleep(300)

        # Sleep between issues if any edits/creations have been made
        if must_sleep:
            print("\tSleeping for 1 second...")
            time.sleep(1)

    print("Referencing parent issue from duplicate issues")
    duplicate_issues = {k: v for k, v in issues.items() if v["parent"]}
    # Set duplicate label
    for issue_id, issue in duplicate_issues.items():
        # Try updating the issue until a success path is hit
        must_sleep = False
        while True:
            try:
                print(
                    "\tReferencing parent issue %s from duplicate issue %s."
                    % (issue["parent"], issue_id)
                )

                # Fetch existing issue
                gh_issue = get_github_issue(repo, issue_id)
                expected_body = issue["body"] + f"\n\nDuplicate of #{issue['parent']}\n"

                if expected_body != gh_issue.body:
                    gh_issue.edit(
                        body=issue["body"] + f"\n\nDuplicate of #{issue['parent']}\n",
                    )
                    must_sleep = True
                else:
                    print("\t\tIssue %s does not need to be updated." % issue_id)

                # Exit the inifinite loop
                break

            except GithubException as e:
                print(e)

                # Sleep for 5 minutes (in case secondary limits have been hit)
                # Don't exit the inifite loop and try again
                time.sleep(300)

        # Sleep between issue updates
        if must_sleep:
            print("\t\tSleeping for 1 second...")
            time.sleep(1)


if __name__ == "__main__":
    main()