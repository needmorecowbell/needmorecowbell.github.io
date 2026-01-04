---
title: "Giggity: GitHub OSINT Reconnaissance Tool"
date: "2019-01-18"
tags: ["python", "security", "osint", "github", "reconnaissance"]
description: "Grab hierarchical data about GitHub organizations, users, or repos - extract emails, names, and repository information through the GitHub API."
---

Giggity is a tool for gathering openly available information about GitHub organizations, users, and repositories. It stores all data in a JSON file organized in a tree of dictionaries for easy analysis or database transfer.

![Giggity Demo](https://user-images.githubusercontent.com/9204902/51312125-3aa4d700-1a53-11e9-89e8-a02063d93595.gif)

## Installation

```bash
pip3 install giggity
```

Or clone the repository:

```bash
pip3 install -r requirements.txt
```

## Usage

```
giggity.py [-h] [-v] [-a] [-u] [-o] [-O OUTPUT] path

positional arguments:
  path                  name of organization or user (or url of repository)

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -a, --authenticate    allows github authentication to avoid ratelimiting
  -u, --user            denotes that given input is a user
  -o, --org             denotes that given input is an organization
  -O OUTPUT, --outfile OUTPUT
                        location to put generated json file
```

### Scraping a User

```bash
python3 giggity.py -a -O needmorecowbell.json -v -u needmorecowbell
```

This will authenticate, scrape the user `needmorecowbell`, and output to `needmorecowbell.json`.

### Scraping an Organization

```bash
python3 giggity.py -a -o github -O github.json
```

Scrape the GitHub organization and output results.

## Using as a Module

Giggity can also be used programmatically:

```python
from giggity import giggity

g = giggity("username", "password")
data = g.getUsers("organization-name", followers=True)

print("List of users in organization: ")
for user, info in data.items():
    print(user)

data = g.getEmails("username", verbose=True)  # Get any emails found
```

## Example Output

When running `python3 giggity.py -a -u geohot -O output.json`:

```json
{
    "emails": [
        "george@comma.ai"
    ],
    "names": [
        "Charles Ellis",
        "George Hotz"
    ],
    "repos": {
        "ORB_SLAM2": {
            "created_at": "2017-04-08T00:21:13Z",
            "description": "ORBSLAM2 running on Mac OS X",
            "fork": true,
            "name": "ORB_SLAM2",
            "updated_at": "2018-10-22T23:51:28Z",
            "url": "https://github.com/geohot/ORB_SLAM2"
        }
    }
}
```

## Note on API Versions

GitHub API still supports v3 (what this script uses), however they are making the shift to GraphQL in v4. Authentication is highly recommended to avoid rate limiting.

Check out the project on [GitHub](https://github.com/needmorecowbell/giggity).
