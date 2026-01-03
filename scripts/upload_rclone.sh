#!/bin/bash
# Upload blog media to S3 using rclone
# Usage: ./upload_rclone.sh

set -e

# Use homes3 for local development, s3 for production
REMOTE="${RCLONE_REMOTE:-homes3}:amblog/assets"
MEDIA_ROOT="$HOME/Media"

echo "=============================================="
echo "Blog Media Upload Script (rclone)"
echo "=============================================="
echo "Remote: $REMOTE"
echo "Media root: $MEDIA_ROOT"
echo ""

# Function to upload a folder with space-to-underscore renaming
upload_folder_renamed() {
    local src="$1"
    local dest="$2"
    local tmp="/tmp/upload_$(basename "$dest")"

    if [[ -d "$src" ]]; then
        echo "Uploading: $src -> $dest"
        rm -rf "$tmp"
        mkdir -p "$tmp"

        # Copy files, replacing spaces with underscores
        for f in "$src"/*; do
            if [[ -f "$f" ]]; then
                fname=$(basename "$f" | tr ' ' '_')
                cp "$f" "$tmp/$fname"
            fi
        done

        rclone copy "$tmp/" "$REMOTE/$dest/" --progress
        rm -rf "$tmp"
    else
        echo "SKIP (not found): $src"
    fi
}

# Function to upload a folder as-is
upload_folder() {
    local src="$1"
    local dest="$2"

    if [[ -d "$src" ]]; then
        echo "Uploading: $src -> $dest"
        rclone copy "$src/" "$REMOTE/$dest/" --progress
    else
        echo "SKIP (not found): $src"
    fi
}

echo ""
echo "=== Project Galleries ==="

# Projects with spaces in filenames (need renaming)
upload_folder_renamed "$MEDIA_ROOT/2020/12/Basement Coral Lab Project" "projects/basement_coral_lab"
upload_folder_renamed "$MEDIA_ROOT/2021/06/vertical rotisserie project" "projects/vertical_rotisserie"
upload_folder_renamed "$MEDIA_ROOT/2015/01/camera glasses project" "projects/rpi_glasses"
upload_folder_renamed "$MEDIA_ROOT/2019/dogwood bonsai project" "projects/dogwood_bonsai"
upload_folder_renamed "$MEDIA_ROOT/2019/hexagon stained glass window" "projects/hexagon_stained_glass_window"
upload_folder_renamed "$MEDIA_ROOT/2019/stained glass plant holder" "projects/stained_glass_plant_holder"
upload_folder_renamed "$MEDIA_ROOT/2019/quarter ring project" "projects/quarter_rings"
upload_folder_renamed "$MEDIA_ROOT/2020/Stained glass woman" "projects/stained_glass_woman_with_hat"
upload_folder_renamed "$MEDIA_ROOT/2020/07/slab computer desk project" "projects/slab_computer_desk"
upload_folder_renamed "$MEDIA_ROOT/2020/12/Zippo Lighter Project" "projects/wood_zippo_lighter"
upload_folder_renamed "$MEDIA_ROOT/2021/03/Garden Bed Project" "projects/raised_bed_project"
upload_folder_renamed "$MEDIA_ROOT/2019/pancetta" "projects/2019_pancetta"
upload_folder_renamed "$MEDIA_ROOT/2025/03/25/stairwell chandelier project" "projects/stairwell_chandelier"

# Projects without spaces (upload as-is)
upload_folder "$MEDIA_ROOT/2014/wii_nunchuck_project" "projects/wii_nunchuck_project"
upload_folder "$MEDIA_ROOT/2014/06/uke" "projects/2014_uke"
upload_folder "$MEDIA_ROOT/2018/bee project" "projects/solitary_bee_tragedy"
upload_folder "$MEDIA_ROOT/2014/uke-coffin" "projects/uke_coffin"

# 2021 Rum Run - single file
echo ""
echo "--- 2021 Rum Run ---"
if [[ -f "$MEDIA_ROOT/2021/02/21-02-21 20-33-58 1096.jpg" ]]; then
    mkdir -p /tmp/upload_rum
    cp "$MEDIA_ROOT/2021/02/21-02-21 20-33-58 1096.jpg" "/tmp/upload_rum/21-02-21_20-33-58_1096.jpg"
    rclone copy /tmp/upload_rum/ "$REMOTE/projects/2021_rum_run/" --progress
    rm -rf /tmp/upload_rum
fi

# Kitchen Island Staining - single file
echo ""
echo "--- Kitchen Island Staining ---"
if [[ -f "$MEDIA_ROOT/2022/05/08/Snapchat-2002572156.jpg" ]]; then
    mkdir -p /tmp/upload_kitchen
    cp "$MEDIA_ROOT/2022/05/08/Snapchat-2002572156.jpg" "/tmp/upload_kitchen/island_finished.jpg"
    rclone copy /tmp/upload_kitchen/ "$REMOTE/projects/kitchen_island_staining/" --progress
    rm -rf /tmp/upload_kitchen
fi

echo ""
echo "=== Kegorator Project (multi-day) ==="
mkdir -p /tmp/upload_kegorator
cp "$MEDIA_ROOT/2024/08/20/kegorator_project/Snapchat-409236232.jpg" "/tmp/upload_kegorator/08_20_initial.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/08/22/kegorator_bartop_project/20240822_182903.jpg" "/tmp/upload_kegorator/08_22_bartop_progress.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/08/22/kegorator_bartop_project/20240822_182920.jpg" "/tmp/upload_kegorator/08_22_bartop_detail.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/08/23/kegorator_bartop_project/20240823_091913.jpg" "/tmp/upload_kegorator/08_23_bartop.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/09/06/kegorator_project/20240906_132736.jpg" "/tmp/upload_kegorator/09_06_complete.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/09/09/kegorator_bartop_project/20240909_104948.jpg" "/tmp/upload_kegorator/09_09_finished_1.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/09/09/kegorator_bartop_project/20240909_105004.jpg" "/tmp/upload_kegorator/09_09_finished_2.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2024/09/09/kegorator_bartop_project/20240909_105035.jpg" "/tmp/upload_kegorator/09_09_finished_3.jpg" 2>/dev/null || true
rclone copy /tmp/upload_kegorator/ "$REMOTE/projects/kegorator/" --progress
rm -rf /tmp/upload_kegorator

echo ""
echo "=== Photography/Travel Galleries ==="
upload_folder_renamed "$MEDIA_ROOT/2017/Puerto Morelos" "img/gallery/travel/puerto_morelos_2017"
upload_folder_renamed "$MEDIA_ROOT/2021/Nashville_july_2021" "img/gallery/travel/nashville_2021"
upload_folder "$MEDIA_ROOT/2021/cross_country" "img/gallery/travel/cross_country_2021"
upload_folder_renamed "$MEDIA_ROOT/2023/04/Nova_Scotia_Trip" "img/gallery/travel/nova_scotia"

# 2024 Erie Birthday Fishing Trip
upload_folder_renamed "$MEDIA_ROOT/2024/10/2024 Birthday Erie Fishing Trip " "photography/2024_erie_birthday"

# 2023 South Myrtle Beach Trip
upload_folder "$MEDIA_ROOT/2023/06/2023_06 South Myrtle Beach Trip" "photography/2023_myrtle_beach"

# 2023 West Virginia Trip
upload_folder_renamed "$MEDIA_ROOT/2023/05/2023_05_16 West Virginia Trip" "photography/2023_west_virginia"

# 2025 Leeper Trip
echo ""
echo "--- 2025 Leeper Trip ---"
mkdir -p /tmp/upload_leeper
cp "$MEDIA_ROOT/2025/02/24/Leeper Trip/Snapchat-1133396925.jpg" "/tmp/upload_leeper/02_24_01.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2025/02/24/Leeper Trip/Snapchat-1444012721.jpg" "/tmp/upload_leeper/02_24_02.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2025/02/24/Leeper Trip/Snapchat-1477595289.jpg" "/tmp/upload_leeper/02_24_03.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2025/02/24/Leeper Trip/Snapchat-1584610376.jpg" "/tmp/upload_leeper/02_24_04.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2025/02/24/Leeper Trip/Snapchat-1843521882.jpg" "/tmp/upload_leeper/02_24_05.jpg" 2>/dev/null || true
cp "$MEDIA_ROOT/2025/02/24/Leeper Trip/Snapchat-1891047842.jpg" "/tmp/upload_leeper/02_24_06.jpg" 2>/dev/null || true
rclone copy /tmp/upload_leeper/ "$REMOTE/photography/2025_leeper/" --progress
rm -rf /tmp/upload_leeper

echo ""
echo "=============================================="
echo "Done! Check output above for any failures."
echo "=============================================="
