#!/bin/bash

sqlite3 \
    ../joss.db \
    "SELECT github_repo_url FROM _joss_paper_project_issues;" | \
    sort | uniq > joss_github_repos.txt
