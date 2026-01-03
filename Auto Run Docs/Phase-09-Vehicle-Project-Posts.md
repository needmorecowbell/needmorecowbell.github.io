# Phase 9: Vehicle Project Posts

This phase publishes truck/vehicle modification project posts using the Obsidian publishing pipeline.

## Content Inventory

| Project | Notes Location | Media Location |
|---------|---------------|----------------|
| Truck Cap Build | `Projects/Truck Camper/2022 Truck Cap Build.md` | `2022/04/truck cap project/` |
| Truck Exhaust Swap | `Projects/2020-12-03 Truck Exhaust Swap.md` | `2020/12/Truck Exhaust Swap Project/` |
| Truck Loudspeaker | `Projects/2019-10-30 Truck Loudspeaker Project.md` | `2019/10/truck loudspeaker project/` |
| DIY Tonneau Cover | N/A | `2021/11/diy tonneau project/` |

## Tasks

- [x] Publish Truck Cap Build post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed:** Created project post with 4 images and 1 video. Media uploaded to MinIO at `projects/truck_cap_build/`. Images analyzed: truck exterior with cap, bed platform construction, LED lighting panel wiring, and finished interior. Video thumbnail generated for interior tour video.

- [x] Publish Truck Exhaust Swap post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed:** Created project post with 1 video. Media uploaded to MinIO at `projects/truck_exhaust_swap/`. Video shows exhaust unboxing with a cat playing with the styrofoam packaging materials. Video thumbnail generated. Images analyzed: 1 video (7 seconds, analyzed via frame extraction).

- [ ] Publish Truck Loudspeaker post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly

- [ ] Publish DIY Tonneau Cover post
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
