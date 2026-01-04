#!/bin/bash
# Generate thumbnails for video files and upload to S3
# Usage: ./generate_video_thumbnails.sh [video_path] [s3_dest_path]
#
# This script:
# 1. Finds all video files (mp4, mov, avi, webm) in the source
# 2. Generates a thumbnail at 1 second mark
# 3. Uploads both video and thumbnail to S3
#
# Thumbnails are named: original_name.thumb.jpg

set -e

REMOTE="${RCLONE_REMOTE:-homes3}:amblog/assets"

# Generate thumbnail for a single video
generate_thumbnail() {
    local video="$1"
    local output="$2"

    # Extract frame at 1 second (or first frame if video is shorter)
    ffmpeg -y -i "$video" -ss 00:00:01 -vframes 1 -q:v 2 "$output" 2>/dev/null || \
    ffmpeg -y -i "$video" -vframes 1 -q:v 2 "$output" 2>/dev/null
}

# Process a single video file
process_video() {
    local video_path="$1"
    local s3_path="$2"

    local basename=$(basename "$video_path")
    local thumb_name="${basename%.*}.thumb.jpg"
    local tmp_thumb="/tmp/$thumb_name"

    echo "Processing: $basename"

    # Generate thumbnail
    if generate_thumbnail "$video_path" "$tmp_thumb"; then
        echo "  Generated thumbnail: $thumb_name"

        # Upload thumbnail
        rclone copyto "$tmp_thumb" "$REMOTE/$s3_path/$thumb_name"
        echo "  Uploaded to: $s3_path/$thumb_name"

        rm -f "$tmp_thumb"
    else
        echo "  ERROR: Failed to generate thumbnail for $basename"
        return 1
    fi
}

# Process all videos in a directory
process_directory() {
    local src_dir="$1"
    local s3_path="$2"

    echo "Processing videos in: $src_dir"
    echo "Destination: $s3_path"
    echo ""

    find "$src_dir" -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.avi" -o -iname "*.webm" \) | while read video; do
        process_video "$video" "$s3_path"
    done
}

# Generate thumbnails for videos already in S3
process_s3_videos() {
    local s3_path="$1"
    local tmp_dir="/tmp/video_thumbs_$$"

    mkdir -p "$tmp_dir"

    echo "Processing S3 videos at: $s3_path"

    # List video files in S3
    rclone lsf "$REMOTE/$s3_path/" 2>/dev/null | grep -iE '\.(mp4|mov|avi|webm)$' | while read video; do
        local thumb_name="${video%.*}.thumb.jpg"

        # Check if thumbnail already exists
        if rclone lsf "$REMOTE/$s3_path/$thumb_name" 2>/dev/null | grep -q .; then
            echo "  SKIP (exists): $thumb_name"
            continue
        fi

        echo "  Downloading: $video"
        rclone copy "$REMOTE/$s3_path/$video" "$tmp_dir/"

        if generate_thumbnail "$tmp_dir/$video" "$tmp_dir/$thumb_name"; then
            echo "  Uploading: $thumb_name"
            rclone copyto "$tmp_dir/$thumb_name" "$REMOTE/$s3_path/$thumb_name"
        fi

        rm -f "$tmp_dir/$video" "$tmp_dir/$thumb_name"
    done

    rm -rf "$tmp_dir"
}

# Main
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <local_path> <s3_dest_path>"
    echo "   or: $0 --s3 <s3_path>  (process videos already in S3)"
    echo ""
    echo "Examples:"
    echo "  $0 ~/Media/2021/videos img/gallery/videos"
    echo "  $0 --s3 img/gallery/travel/brawl-under-the-bridge-2021"
    exit 1
fi

if [[ "$1" == "--s3" ]]; then
    process_s3_videos "$2"
else
    process_directory "$1" "$2"
fi

echo ""
echo "Done!"
