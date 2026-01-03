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
| Vigiles and Grafana Dashboards | `Blog/2022-04-06-vigiles-and-grafana-dashboards.md` | Review needed |

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

- [ ] Decide on Coding Livestream series approach
  - Option A: Publish as 4 separate posts
  - Option B: Consolidate into single "Coding Livestream Series" post
  - Option C: Skip if content is too dated
  - Review each post for relevance and accuracy

- [ ] If publishing Coding Livestream posts:
  - [ ] Publish Livestream 1: Find Every Arby's
  - [ ] Publish Livestream 2: SSH Honeypot
  - [ ] Publish Livestream 3: YARA
  - [ ] Publish Livestream 4: Computer Vision

- [ ] Review and publish Vigiles/Grafana post
  - Review content for accuracy
  - Check if Vigiles references are still valid
  - Update if needed
  - Publish via pipeline

## Notes

- These are older posts (2017-2022) that may need updating
- Tech content can become dated quickly - review for accuracy
- Some posts may reference tools/services that no longer exist
- Consider adding disclaimers for dated content
