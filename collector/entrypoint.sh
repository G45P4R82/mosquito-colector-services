#!/bin/sh
set -eu

uid="${DOCKER_UID:-1000}"
gid="${DOCKER_GID:-1000}"

chown -R "${uid}:${gid}" /logs
exec gosu "${uid}:${gid}" python "$@"
