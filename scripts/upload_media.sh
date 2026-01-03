#!/bin/bash
# Upload blog media to MinIO
# Run this after installing minio-client: yay -S minio-client
#
# Usage: ./upload_media.sh
#
# This script uploads media from ~/Media to MinIO bucket with the path structure
# expected by the blog (s3cdn.617a.net/amblog/assets/...)

set -e

# Load config
source "$(dirname "$0")/.env"

# Configure mc alias if not exists
MC_ALIAS="blog"
if ! mc alias list | grep -q "^${MC_ALIAS}"; then
    echo "Configuring MinIO alias..."
    PROTOCOL="http"
    [[ "$MINIO_SECURE" == "true" ]] && PROTOCOL="https"
    mc alias set "$MC_ALIAS" "${PROTOCOL}://${MINIO_ENDPOINT}" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
fi

BUCKET="${MC_ALIAS}/${MINIO_BUCKET}"
MEDIA_ROOT="$HOME/Media"

echo "=============================================="
echo "Blog Media Upload Script"
echo "=============================================="
echo "Bucket: $BUCKET"
echo "Media root: $MEDIA_ROOT"
echo ""

# Function to upload a folder
upload_folder() {
    local src="$1"
    local dest="$2"

    if [[ -d "$src" ]]; then
        echo "Uploading: $src -> $dest"
        mc cp --recursive "$src/" "${BUCKET}/${dest}/"
    else
        echo "SKIP (not found): $src"
    fi
}

# Function to upload a single file
upload_file() {
    local src="$1"
    local dest="$2"

    if [[ -f "$src" ]]; then
        echo "Uploading: $src -> $dest"
        mc cp "$src" "${BUCKET}/${dest}"
    else
        echo "SKIP (not found): $src"
    fi
}

echo ""
echo "=== Blog Post Images ==="

# Goodwill Chest images (Blog pics folder - these need renaming)
echo ""
echo "--- Goodwill Chest Part 1 (2017-01-19) ---"
echo "NOTE: These files need to be manually renamed to match expected paths:"
echo "  Source: ~/Media/Blog pics/20170119_*.jpg"
echo "  Expected paths in blog:"
echo "    img/goodwill-chest/post-goodwill-chest-closed.jpg"
echo "    img/goodwill-chest/post-goodwill-psu.jpg"
echo "    img/goodwill-chest/post-goodwill-chest-side-sanded.jpg"
echo "    img/goodwill-chest/post-goodwill-chest-inner.jpg"
echo ""
echo "  Available source files:"
ls -1 "$MEDIA_ROOT/Blog pics/"20170119*.jpg 2>/dev/null || echo "  (none found)"

echo ""
echo "--- Goodwill Chest Part 2 (2017-07-21) ---"
echo "  Source: ~/Media/Blog pics/Goodwill-chest part 2/"
ls -1 "$MEDIA_ROOT/Blog pics/Goodwill-chest part 2/" 2>/dev/null || echo "  (none found)"

echo ""
echo "--- QR Guitar Project ---"
echo "  Source: ~/Media/2015/qr-guitar project/"
echo "  Expected: img/post-qrGuitar-GIF.gif (need to create GIF from video/images)"

echo ""
echo "=== Project Galleries ==="

# These are nanogallery folders - upload entire directories
upload_folder "$MEDIA_ROOT/2014/wii_nunchuck_project" "projects/wii_nunchuck_project"
upload_folder "$MEDIA_ROOT/2014/06/uke" "projects/2014_uke"
upload_folder "$MEDIA_ROOT/2015/01/camera glasses project" "projects/rpi_glasses"
upload_folder "$MEDIA_ROOT/2018/bee project" "projects/solitary_bee_tragedy"
upload_folder "$MEDIA_ROOT/2019/dogwood bonsai project" "projects/dogwood_bonsai"
upload_folder "$MEDIA_ROOT/2019/hexagon stained glass window" "projects/hexagon_stained_glass_window"
upload_folder "$MEDIA_ROOT/2019/stained glass plant holder" "projects/stained_glass_plant_holder"
upload_folder "$MEDIA_ROOT/2019/quarter ring project" "projects/quarter_rings"
upload_folder "$MEDIA_ROOT/2020/Stained glass woman" "projects/stained_glass_woman_with_hat"
upload_folder "$MEDIA_ROOT/2020/07/slab computer desk project" "projects/slab_computer_desk"
upload_folder "$MEDIA_ROOT/2020/12/Zippo Lighter Project" "projects/wood_zippo_lighter"
upload_folder "$MEDIA_ROOT/2021/03/Garden Bed Project" "projects/raised_bed_project"
upload_folder "$MEDIA_ROOT/2021/06/vertical rotisserie project" "projects/vertical_rotisserie"
upload_folder "$MEDIA_ROOT/2019/pancetta" "projects/2019_pancetta"

# Basement Coral Lab - frag tank for studying light refraction
echo ""
echo "--- Basement Coral Lab ---"
mkdir -p /tmp/basement_coral_lab
for f in "$MEDIA_ROOT/2020/12/Basement Coral Lab Project/"*; do
    fname=$(basename "$f" | tr ' ' '_')
    cp "$f" "/tmp/basement_coral_lab/$fname" 2>/dev/null || true
done
upload_folder "/tmp/basement_coral_lab" "projects/basement_coral_lab"
rm -rf /tmp/basement_coral_lab

# 2021 Rum Run - individual files from 2021/02
echo ""
echo "--- 2021 Rum Run ---"
mkdir -p /tmp/2021_rum_run
cp "$MEDIA_ROOT/2021/02/21-02-21 20-33-58 1096.jpg" "/tmp/2021_rum_run/21-02-21_20-33-58_1096.jpg" 2>/dev/null || true
upload_folder "/tmp/2021_rum_run" "projects/2021_rum_run"
rm -rf /tmp/2021_rum_run

echo ""
echo "=== Photography/Travel Galleries ==="

upload_folder "$MEDIA_ROOT/2017/Puerto Morelos" "img/gallery/travel/puerto_morelos_2017"
upload_folder "$MEDIA_ROOT/2021/Nashville_july_2021" "img/gallery/travel/nashville_2021"
upload_folder "$MEDIA_ROOT/2021/cross_country" "img/gallery/travel/cross_country_2021"
upload_folder "$MEDIA_ROOT/2023/04/Nova_Scotia_Trip" "img/gallery/travel/nova_scotia"

# brawl-under-the-bridge might need to be found
echo ""
echo "NOTE: brawl-under-the-bridge-2021 gallery not found in Media folder"
echo "      Search for it manually if needed"

echo ""
echo "=== Other Assets ==="
echo "These need manual handling:"
echo "  - img/resume.jpg - Need to find or create"
echo "  - videos/twilightzone.mp4 - Need to find source"
echo "  - img/prof.jpg (profile picture)"
echo ""

echo "=============================================="
echo "Done! Check output above for any failures."
echo "=============================================="
