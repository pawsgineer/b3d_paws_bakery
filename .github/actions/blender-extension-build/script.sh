set -ex

NON_SET_MSG="must be set and non-empty"

: ${BL_VERSION:?BL_VERSION $NON_SET_MSG}
: ${BL_EXT_NAME:?BL_EXT_NAME $NON_SET_MSG}

EXT_VERSION=$(sed -n "s/^version\s*=\s*\"\(.*\)\"/\1/p" \
    ./src/${BL_EXT_NAME}/blender_manifest.toml)
echo "Building extension ${BL_EXT_NAME}-${EXT_VERSION} with Blender: ${BL_VERSION}"

docker run \
    -v "$(pwd):/repo" \
    --entrypoint bash \
    lscr.io/linuxserver/blender:${BL_VERSION} \
    -c "\
        cd /repo;
        blender \
            --factory-startup \
            --command extension build \
            --verbose \
            --source-dir /repo/src/${BL_EXT_NAME} \
    "

ls -lh
test -f "${BL_EXT_NAME}-${EXT_VERSION}.zip"

echo "version=${EXT_VERSION}" >> "$GITHUB_OUTPUT"
