---
title: Testing Various Date String Formats
date: January 15, 2024
publish: true
tags:
  - dates
  - testing
---

# Testing Various Date String Formats

This post uses a human-readable date format "January 15, 2024" which should be
normalized to ISO format "2024-01-15" by the frontmatter transformer.

Other formats that might be used:
- 2024/01/15
- 15 Jan 2024
- Jan 15, 2024
- 2024-01-15T10:30:00-05:00

All should be handled gracefully.
