---
title: "Sniff-Paste: Pastebin OSINT Harvester"
date: "2019-01-19"
tags: ["python", "security", "osint", "pastebin", "scraping"]
description: "A multithreaded Pastebin scraper that collects pastes and harvests emails, IPs, phone numbers, and cryptocurrency addresses."
---

Sniff-Paste is a multithreaded Pastebin scraper that collects pastes into a MySQL database, then analyzes them for noteworthy information like IP addresses, emails, phone numbers, and cryptocurrency addresses.

![Sniff-Paste](https://github.com/needmorecowbell/sniff-paste/raw/master/res/sniff-paste-pic.jpg)

## How It Works

The scraper can be set to a paste limit of 0 to scrape indefinitely. When running indefinitely, press `Ctrl+C` to stop - all useful information will be in the database with links back to the original pastes.

## Installation

```bash
sudo apt install libxslt-dev python3-lxml python3-nmap xsltproc mysql-server
pip3 install -r requirements.txt
```

Then:
1. Create a database named `sniff_paste` in MySQL
2. Fill in `settings.ini` with your configuration
3. Run `python3 sniff-paste.py`

This will scrape Pastebin for the latest pastes, then run analysis for IP addresses, emails, and phone numbers. It filters out duplicates and runs scans on harvested data.

## Database Structure

The `sniff_paste` database contains these tables:

| Table | Contents |
|-------|----------|
| `pastes` | Full paste text, date, link, title, language |
| `emails` | Email addresses with paste reference |
| `links` | URLs with paste reference |
| `ip` | IP addresses with connectivity status |
| `phones` | Phone numbers with paste reference |
| `secrets` | Secret types (keys, tokens) with paste reference |
| `ports` | Port scan info (port, status, service, version, IP) |
| `cryptos` | Cryptocurrency addresses with paste reference |

**Note:** Crypto findings are not certain to be valid - consider them low probability findings.

## What It Finds

- **Email addresses** - Extracted and deduplicated
- **IP addresses** - With optional connectivity checks
- **Phone numbers** - Various formats
- **URLs** - Links found in pastes
- **Secrets** - API keys, private keys, tokens
- **Cryptocurrency addresses** - Bitcoin, Ethereum, etc.

## Future Plans

This tool is being integrated into a larger project called [Funnel](https://github.com/needmorecowbell/Funnel), which aims to consolidate all my OSINT tools into one streamlined solution.

Check out the project on [GitHub](https://github.com/needmorecowbell/sniff-paste).
