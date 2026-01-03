# Phase 8: Craft Project Posts

This phase publishes high-quality craft/maker project posts using the Obsidian publishing pipeline established in Phase 7.

## Content Inventory

| Project | Notes Location | Media Location | Photos |
|---------|---------------|----------------|--------|
| Slab Computer Desk | `Projects/Slab Computer Desk.md` | `2020/07/slab computer desk project/` | 8 (published) |
| Wood Zippo Lighter | `Projects/Wood Zippo Lighter.md` | `2020/12/Zippo Lighter Project/` | Yes |
| Quarter Rings | `Projects/Quarter Rings.md` | `2019/quarter ring project/` | Yes |
| Stained Glass Hexagon | `Projects/Stained Glass hexagon window.md` | `2019/hexagon stained glass window/` | Yes |
| Stained Glass Plant Holder | `Projects/Stained Glass Plant Holder.md` | `2019/stained glass plant holder/` | Yes |
| Dogwood Bonsai | `Projects/Dogwood Bonsai Project.md` | `2019/dogwood bonsai project/` | Yes |
| Sumac Wine | N/A | `2023/08/2023_08_14 Sumac Wine Project/` | Yes |
| Stairwell Chandelier | N/A | `2025/03/25/stairwell chandelier project/` | Yes |
| Porch Reflooring | N/A | `2024/09/porch_reflooring_project/` | Yes |
| Tiramisu Project | N/A | `2022/12/2022_12_27 Tiramisu Project/` | Yes |

## Tasks

- [x] Publish Slab Computer Desk post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed**: Enriched Obsidian note with materials list, build process description, and corrected date. Uploaded 8 images to MinIO (10 missing images from the original note were removed). Hugo post generated at `content/english/projects/slab-computer-desk.md`.

- [x] Publish Wood Zippo Lighter post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed**: Enriched Obsidian note with materials list, build process, results, and lessons learned sections. Uploaded 7 images to MinIO. Hugo post generated at `content/english/projects/wood-zippo-lighter.md`.

- [x] Publish Stained Glass Hexagon Window post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed**: Enriched Obsidian note with materials list, build process, results, and lessons learned sections. Added `content_type: project` to frontmatter and removed 2 references to missing video files. Uploaded 7 images and 2 videos to MinIO (9 files total). Generated video thumbnails. Hugo post generated at `content/english/projects/stained-glass-hexagon-window.md`.

- [x] Publish Quarter Rings post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed**: Enriched Obsidian note with materials list, build process description, results, and lessons learned sections. Added `content_type: project` to frontmatter. Uploaded 8 images and 1 video to MinIO (9 files total). Generated video thumbnail. Removed old nanogallery2-based post and replaced with new Hugo post at `content/english/projects/quarter-rings.md`.

- [ ] Publish Sumac Wine post
  - Create Obsidian note if not exists
  - Enrich content
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly

- [ ] Publish Porch Reflooring post
  - Create Obsidian note if not exists
  - Enrich content
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly

- [ ] Publish Stairwell Chandelier post
  - Create Obsidian note if not exists
  - Enrich content
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly

## Notes

- All media is located in `~/Media/` (symlinked from `~/Notes/Media`)
- Filenames with spaces must be converted to underscores for URLs
- Video thumbnails must be generated for any video content
- Do not mention other people by name (privacy)
