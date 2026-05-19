#!/bin/bash
# Generate thumbnails for images and videos, then upload to S3
# Usage: ./generate_thumbnails.sh <local_path> <s3_dest_path>
#    or: ./generate_thumbnails.sh --s3 <s3_path>  (process files already in S3)
#
# This script:
# 1. Finds all media files (images and videos)
# 2. Generates thumbnails:
#    - Images: resized to 400px width, JPEG quality 85
#    - Videos: frame extracted at 1 second mark
# 3. Uploads both originals and thumbnails to S3
#
# Thumbnails are named: original_name.thumb.jpg
# For example: my_photo.jpg -> my_photo.thumb.jpg
#              my_video.mp4 -> my_video.thumb.jpg

set -e

REMOTE="${RCLONE_REMOTE:-homes3}:amblog/assets"
THUMB_WIDTH="${THUMB_WIDTH:-400}"
THUMB_QUALITY="${THUMB_QUALITY:-85}"

# Image extensions to process
IMAGE_EXTENSIONS="jpg|jpeg|png|gif|webp|JPG|JPEG|PNG|GIF|WEBP"
# Video extensions to process
VIDEO_EXTENSIONS="mp4|mov|avi|webm|MP4|MOV|AVI|WEBM"

# Generate thumbnail for an image using ImageMagick
generate_image_thumbnail() {
    local image="$1"
    local output="$2"

    # Resize to thumbnail width, maintaining aspect ratio
    # Use JPEG output with specified quality
    convert "$image" \
        -resize "${THUMB_WIDTH}x>" \
        -quality "$THUMB_QUALITY" \
        -strip \
        "$output" 2>/dev/null
}

# Generate thumbnail for a video using ffmpeg
generate_video_thumbnail() {
    local video="$1"
    local output="$2"

    # Extract frame at 1 second (or first frame if video is shorter)
    # Then resize to match image thumbnail width
    ffmpeg -y -i "$video" -ss 00:00:01 -vframes 1 \
        -vf "scale=${THUMB_WIDTH}:-1" \
        -q:v 2 "$output" 2>/dev/null || \
    ffmpeg -y -i "$video" -vframes 1 \
        -vf "scale=${THUMB_WIDTH}:-1" \
        -q:v 2 "$output" 2>/dev/null
}

# Process a single file (image or video)
process_file() {
    local file_path="$1"
    local s3_path="$2"
    local is_video="$3"

    local basename=$(basename "$file_path")
    local name_no_ext="${basename%.*}"
    local thumb_name="${name_no_ext}.thumb.jpg"
    local tmp_thumb="/tmp/$thumb_name"

    echo "Processing: $basename"

    # Generate thumbnail based on file type
    if [[ "$is_video" == "true" ]]; then
        if generate_video_thumbnail "$file_path" "$tmp_thumb"; then
            echo "  Generated video thumbnail: $thumb_name"
        else
            echo "  ERROR: Failed to generate thumbnail for $basename"
            return 1
        fi
    else
        if generate_image_thumbnail "$file_path" "$tmp_thumb"; then
            echo "  Generated image thumbnail: $thumb_name"
        else
            echo "  ERROR: Failed to generate thumbnail for $basename"
            return 1
        fi
    fi

    # Upload thumbnail
    if [[ -f "$tmp_thumb" ]]; then
        rclone copyto "$tmp_thumb" "$REMOTE/$s3_path/$thumb_name"
        echo "  Uploaded to: $s3_path/$thumb_name"
        rm -f "$tmp_thumb"
    fi
}

# Process all media files in a directory
process_directory() {
    local src_dir="$1"
    local s3_path="$2"

    echo "Processing media in: $src_dir"
    echo "Destination: $s3_path"
    echo "Thumbnail width: ${THUMB_WIDTH}px"
    echo ""

    # Process images
    find "$src_dir" -type f -regextype posix-extended -iregex ".*\.($IMAGE_EXTENSIONS)$" | while read file; do
        process_file "$file" "$s3_path" "false"
    done

    # Process videos
    find "$src_dir" -type f -regextype posix-extended -iregex ".*\.($VIDEO_EXTENSIONS)$" | while read file; do
        process_file "$file" "$s3_path" "true"
    done
}

# Process media files already in S3
process_s3_media() {
    local s3_path="$1"
    local tmp_dir="/tmp/media_thumbs_$$"

    mkdir -p "$tmp_dir"

    echo "Processing S3 media at: $s3_path"
    echo "Thumbnail width: ${THUMB_WIDTH}px"
    echo ""

    # List all files in S3
    rclone lsf "$REMOTE/$s3_path/" 2>/dev/null | while read file; do
        local name_no_ext="${file%.*}"
        local ext="${file##*.}"
        local thumb_name="${name_no_ext}.thumb.jpg"

        # Skip if already a thumbnail
        if [[ "$file" == *.thumb.jpg ]]; then
            continue
        fi

        # Check if thumbnail already exists
        if rclone lsf "$REMOTE/$s3_path/$thumb_name" 2>/dev/null | grep -q .; then
            echo "SKIP (exists): $thumb_name"
            continue
        fi

        # Determine if image or video
        local is_video="false"
        if echo "$ext" | grep -qiE "^($VIDEO_EXTENSIONS)$"; then
            is_video="true"
        elif echo "$ext" | grep -qiE "^($IMAGE_EXTENSIONS)$"; then
            is_video="false"
        else
            # Unknown extension, skip
            continue
        fi

        echo "Downloading: $file"
        rclone copy "$REMOTE/$s3_path/$file" "$tmp_dir/"

        if [[ "$is_video" == "true" ]]; then
            if generate_video_thumbnail "$tmp_dir/$file" "$tmp_dir/$thumb_name"; then
                echo "  Uploading: $thumb_name"
                rclone copyto "$tmp_dir/$thumb_name" "$REMOTE/$s3_path/$thumb_name"
            fi
        else
            if generate_image_thumbnail "$tmp_dir/$file" "$tmp_dir/$thumb_name"; then
                echo "  Uploading: $thumb_name"
                rclone copyto "$tmp_dir/$thumb_name" "$REMOTE/$s3_path/$thumb_name"
            fi
        fi

        rm -f "$tmp_dir/$file" "$tmp_dir/$thumb_name"
    done

    rm -rf "$tmp_dir"
}

# Upload a single file with thumbnail generation
upload_with_thumbnail() {
    local file_path="$1"
    local s3_path="$2"

    local basename=$(basename "$file_path")
    local ext="${basename##*.}"
    local name_no_ext="${basename%.*}"
    local thumb_name="${name_no_ext}.thumb.jpg"
    local tmp_thumb="/tmp/$thumb_name"

    # Determine if image or video
    local is_video="false"
    if echo "$ext" | grep -qiE "^($VIDEO_EXTENSIONS)$"; then
        is_video="true"
    elif echo "$ext" | grep -qiE "^($IMAGE_EXTENSIONS)$"; then
        is_video="false"
    else
        echo "Unknown media type: $basename"
        return 1
    fi

    echo "Uploading: $basename"

    # Upload original
    rclone copyto "$file_path" "$REMOTE/$s3_path/$basename"
    echo "  Uploaded original"

    # Generate and upload thumbnail
    if [[ "$is_video" == "true" ]]; then
        if generate_video_thumbnail "$file_path" "$tmp_thumb"; then
            rclone copyto "$tmp_thumb" "$REMOTE/$s3_path/$thumb_name"
            echo "  Uploaded thumbnail: $thumb_name"
            rm -f "$tmp_thumb"
        fi
    else
        if generate_image_thumbnail "$file_path" "$tmp_thumb"; then
            rclone copyto "$tmp_thumb" "$REMOTE/$s3_path/$thumb_name"
            echo "  Uploaded thumbnail: $thumb_name"
            rm -f "$tmp_thumb"
        fi
    fi
}

# Show help
show_help() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  <local_path> <s3_path>   Process local directory, generate thumbs, upload all"
    echo "  --s3 <s3_path>           Generate thumbnails for files already in S3"
    echo "  --file <file> <s3_path>  Upload single file with thumbnail"
    echo ""
    echo "Environment variables:"
    echo "  THUMB_WIDTH    Thumbnail width in pixels (default: 400)"
    echo "  THUMB_QUALITY  JPEG quality 1-100 (default: 85)"
    echo "  RCLONE_REMOTE  Rclone remote name (default: homes3)"
    echo ""
    echo "Examples:"
    echo "  $0 ~/Media/my_project projects/my_project"
    echo "  $0 --s3 projects/my_project"
    echo "  $0 --file ~/Media/photo.jpg projects/my_project"
    echo ""
    echo "Requires: ImageMagick (convert), ffmpeg, rclone"
}

# Check dependencies
check_deps() {
    local missing=""
    command -v convert >/dev/null || missing="$missing ImageMagick(convert)"
    command -v ffmpeg >/dev/null || missing="$missing ffmpeg"
    command -v rclone >/dev/null || missing="$missing rclone"

    if [[ -n "$missing" ]]; then
        echo "ERROR: Missing dependencies:$missing"
        exit 1
    fi
}

# Main
if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

check_deps

case "$1" in
    --help|-h)
        show_help
        ;;
    --s3)
        if [[ -z "$2" ]]; then
            echo "ERROR: --s3 requires an S3 path"
            exit 1
        fi
        process_s3_media "$2"
        ;;
    --file)
        if [[ -z "$2" || -z "$3" ]]; then
            echo "ERROR: --file requires <file_path> and <s3_path>"
            exit 1
        fi
        upload_with_thumbnail "$2" "$3"
        ;;
    *)
        if [[ -z "$2" ]]; then
            echo "ERROR: Requires both local path and S3 destination path"
            exit 1
        fi
        process_directory "$1" "$2"
        ;;
esac

echo ""
echo "Done!"
