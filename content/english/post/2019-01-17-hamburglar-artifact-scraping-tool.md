---
title: "Hamburglar: Collect Useful Information from URLs, Directories, and Files"
date: "2019-01-17"
tags: ["python", "security", "osint", "regex", "yara"]
description: "A multithreaded scraping tool for artifact retrieval - find emails, IPs, private keys, and more using regex and YARA rules."
---

Hamburglar is a tool I built to recursively scrape directories, files, URLs, and git repos for useful artifacts like emails, IP addresses, private keys, and cryptocurrency addresses. It uses regex filters and YARA rules to find noteworthy information.

![Hamburglar Demo](https://user-images.githubusercontent.com/7833164/51336290-29a79600-1a52-11e9-96a1-beac9207fdab.gif)

## Two Versions

**Hamburglar (Full)** - Full fledged scraping tool with all features:

```bash
pip3 install -r requirements.txt
```

**Hamburglar Lite** - Single script, no dependencies, designed to be quickly downloaded and executed:

```bash
wget https://raw.githubusercontent.com/needmorecowbell/Hamburglar/hamburglar-lite/hamburglar-lite.py
```

## Usage

```
usage: hamburglar.py [-h] [-g] [-x] [-v] [-w] [-i] [-o FILE] [-y YARA] path

positional arguments:
  path                  path to directory, url, or file, depending on flag used

optional arguments:
  -h, --help            show this help message and exit
  -g, --git             sets hamburglar into git mode
  -x, --hexdump         give hexdump of file
  -v, --verbose         increase output verbosity
  -w, --web             sets Hamburgler to web request mode, enter url as path
  -i, --ioc             uses iocextract to parse contents
  -o FILE, --out FILE   write results to FILE
  -y YARA, --yara YARA  use yara ruleset for checking
```

### Directory Traversal

```bash
python3 hamburglar.py ~/Directory/
```

Recursively scans for files and analyzes each for findings using regex filters.

### Git Scraping Mode

```bash
python3 hamburglar.py -g https://www.github.com/needmorecowbell/Hamburglar
```

Clone and scan a git repository. Add `-y <rulepath>` to use YARA rules.

### Web Request Mode

```bash
python3 hamburglar.py -w https://google.com
```

Analyze HTML content from a URL.

### IOC Extraction

```bash
python3 hamburglar.py -w -i https://pastebin.com/SYisR95m
```

Extract indicators of compromise using iocextract.

### YARA Rule Analysis

```bash
python3 hamburglar.py -y rules/ ~/Directory
```

Compile YARA rules and check against every item in the directory.

## What Hamburglar Can Find

- IPv4 addresses (public and local)
- Email addresses
- Private keys
- URLs
- IOCs (using iocextract)
- Cryptocurrency addresses
- Anything you can imagine using regex filters and YARA rules

## Example Output

```json
{
    "/home/adam/Dev/test/email.txt": {
        "emails": "{'testingtesting@gmail.com'}"
    },
    "/home/adam/Dev/test/ips.txt": {
        "ipv4": "{'10.0.11.2', '192.168.1.1'}"
    },
    "/home/adam/Dev/test/test2/links.txt": {
        "site": "{'http://login.web.com'}"
    }
}
```

## Settings

- `whitelistOn`: turns on or off whitelist checking
- `maxWorkers`: number of worker threads to run concurrently
- `whitelist`: list of files or directories to exclusively scan
- `blacklist`: list of files, extensions, or directories to block
- `regexList`: dictionary of regex filters with filter type as the key

Check out the project on [GitHub](https://github.com/needmorecowbell/Hamburglar).
