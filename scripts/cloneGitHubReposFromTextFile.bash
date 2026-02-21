#!/bin/bash
set -euo pipefail

input_file=$1
dry_run="false"

usage() {
  cat <<"EOF"
Usage: ./clone_github_repos.sh [-n]

Options:
  -n    Dry run (print actions without cloning)
  -h    Show this help
EOF
}

while getopts ":nh" opt; do
  case "$opt" in
    n)
      dry_run="true"
      ;;
    h)
      usage
      exit 0
      ;;
    \?)
      echo "Unknown option: -$OPTARG" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$input_file" ]]; then
  echo "Missing input file: $input_file" >&2
  exit 1
fi

current_dir="$(pwd)"
echo "This will clone GitHub repositories into: $current_dir"
read -r -p "Continue? [y/N] " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

trim_whitespace() {
  local value="$1"
  value="${value#${value%%[![:space:]]*}}"
  value="${value%${value##*[![:space:]]}}"
  printf "%s" "$value"
}

normalize_github_url() {
  local url="$1"
  url="${url%/}"
  url="${url%.git}"
  printf "%s" "$url"
}

extract_owner_repo() {
  local url="$1"
  local trimmed="${url#http://}"
  trimmed="${trimmed#https://}"
  trimmed="${trimmed#github.com/}"
  local owner="${trimmed%%/*}"
  local rest="${trimmed#*/}"
  local repo="${rest%%/*}"
  if [[ -z "$owner" || -z "$repo" ]]; then
    return 1
  fi
  printf "%s/%s" "$owner" "$repo"
}

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue

  url_part="${line#*|}"
  url_part="$(trim_whitespace "$url_part")"
  [[ -z "$url_part" ]] && continue

  if [[ "$url_part" != http*://github.com/* ]]; then
    continue
  fi

  normalized_url="$(normalize_github_url "$url_part")"
  if ! owner_repo="$(extract_owner_repo "$normalized_url")"; then
    echo "Skipping malformed GitHub URL: $url_part" >&2
    continue
  fi

  owner="${owner_repo%%/*}"
  repo="${owner_repo#*/}"
  target_dir="$owner/$repo"

  if [[ -d "$target_dir" ]]; then
    echo "Skipping existing repo: $target_dir"
    continue
  fi

  if [[ "$dry_run" == "true" ]]; then
    echo "[dry-run] mkdir -p $owner"
    echo "[dry-run] git clone $normalized_url $target_dir"
    continue
  fi

  mkdir -p "$owner"
  git clone "$normalized_url" "$target_dir"
done < "$input_file"
