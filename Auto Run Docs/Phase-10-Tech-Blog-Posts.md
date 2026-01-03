# Phase 10: Tech Blog Posts

This phase reviews and publishes tech-focused blog posts from the Notes/Blog folder.

## Content Inventory

| Post | Location | Status |
|------|----------|--------|
| Linux Tips: Easy Aliases | `Blog/2017-08-01-linux-tips-easy-aliases.md` | Ready to publish |
| On the Future of Apps | `Blog/2017-08-07-on-the-future-of-apps.md` | Review needed - may be dated |
| Coding Livestream 1: Find Every Arby's | `Blog/2018-11-13-coding-livestream-1-find-every-arby-s-in-america.md` | Review needed |
| Coding Livestream 2: SSH Honeypot | `Blog/2018-11-13-coding-livestream-2-let-s-deploy-an-ssh-honeypot.md` | Review needed |
| Coding Livestream 3: YARA | `Blog/2018-11-13-coding-livestream-3-let-s-learn-about-yara.md` | Review needed |
| Coding Livestream 4: Computer Vision | `Blog/2018-11-13-coding-livestream-4-computer-vision-on-public-ip-cams.md` | Review needed |
| Vigiles and Grafana Dashboards | `Blog/2022-04-06-vigiles-and-grafana-dashboards.md` | Skipped - empty stub, no content |

## Tasks

- [x] Review and publish Linux Tips: Easy Aliases post
  - Review content for accuracy
  - Update if needed
  - Publish via pipeline or direct copy
  - Verify renders correctly
  - **Completed:** Post was already in content folder. Fixed typos (begginning, exessively), corrected duplicate volmute alias (now volmute/volunmute), improved markdown formatting with proper headers and bash code blocks, cleaned up frontmatter. Hugo build verified successful.

- [x] Review On the Future of Apps post
  - Assess if content is still relevant (2017 post)
  - Decide: update, publish as-is, or skip
  - If publishing, run through pipeline
  - **Completed:** Post was already in content folder. The 2017 predictions about streaming/cloud computing have aged well (cloud gaming, Chromebooks, etc. are now mainstream). Improvements made: Fixed typo "ths" → "this", corrected "IWannaCry" → "WannaCry", converted HTML `<b>` tags to markdown `**`, capitalized "4g" → "4G" and "raspberry pi" → "Raspberry Pi", added proper markdown headers for structure, replaced raw HTML YouTube embed with Hugo shortcode `{{< youtube >}}`, added context note at top explaining this is a 2017 retrospective piece. Hugo build verified successful.

- [x] Decide on Coding Livestream series approach
  - Option A: Publish as 4 separate posts
  - Option B: Consolidate into single "Coding Livestream Series" post
  - Option C: Skip if content is too dated
  - Review each post for relevance and accuracy
  - **Decision: Option A - Published as 4 separate posts.** Posts were already in content folder. Topics remain relevant: web scraping techniques, SSH honeypots (Cowrie still actively maintained), YARA rules (industry standard for malware detection), and computer vision fundamentals. Posts are linked via `series: coding-livestream` tag.

- [x] If publishing Coding Livestream posts:
  - [x] Publish Livestream 1: Find Every Arby's
  - [x] Publish Livestream 2: SSH Honeypot
  - [x] Publish Livestream 3: YARA
  - [x] Publish Livestream 4: Computer Vision
  - **Completed:** All 4 posts updated with: (1) Replaced raw HTML iframe embeds with Hugo `{{< youtube >}}` shortcodes, (2) Added context note indicating 2018 livestream series, (3) Added descriptive headers and topic bullet points for each post, (4) Added relevant links (Cowrie GitHub, YARA docs). Hugo build verified successful.

- [x] Review and publish Vigiles/Grafana post
  - Review content for accuracy
  - Check if Vigiles references are still valid
  - Update if needed
  - Publish via pipeline
  - **Skipped:** Source file at `/home/adam/Notes/Blog/2022-04-06-vigiles-and-grafana-dashboards.md` contains only a title stub ("Elegant Security Monitoring Dashboards using Grafana and the Vigiles API Toolkit") with no actual content. The post appears to have been a draft idea that was never written. Cannot publish without content.

## Notes

- These are older posts (2017-2022) that may need updating
- Tech content can become dated quickly - review for accuracy
- Some posts may reference tools/services that no longer exist
- Consider adding disclaimers for dated content
