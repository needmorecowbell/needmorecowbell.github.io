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

- [x] Publish Truck Loudspeaker post
  - Enrich content in Obsidian note if needed
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed:** Created project post with 2 videos. Media uploaded to MinIO at `projects/truck_loudspeaker/`. Videos show PA system components and operation: 1) ~10 second demo of amplifier wiring and setup, 2) ~4 second demo of horn speaker connected to amplifier. Video thumbnails generated. Videos analyzed: 6 frames extracted across 2 videos for content analysis.

- [x] Publish DIY Tonneau Cover post
  - Create Obsidian note if not exists
  - Enrich content
  - Upload images to MinIO
  - Generate Hugo post via pipeline
  - Verify renders correctly
  - **Completed:** Created project post with 2 images. Media uploaded to MinIO at `projects/diy_tonneau_cover/`. Images analyzed: side view showing F-150 with DIY soft tonneau cover installed, rear view showing tarp-style cover stretched across truck bed. No existing Obsidian note found - content written directly as Hugo post based on image analysis. Images analyzed: 2

## Notes

- All media is located in `~/Media/` (symlinked from `~/Notes/Media`)
- Filenames with spaces must be converted to underscores for URLs
- Video thumbnails must be generated for any video content
- Do not mention other people by name (privacy)
