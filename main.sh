#!/usr/bin/env bash

set -e

cmd_build() {
  git_branch=$(git rev-parse --abbrev-ref HEAD)
  short_hash=$(git rev-parse --short HEAD)
  tags="-t 864879987165.dkr.ecr.us-east-1.amazonaws.com/calm/localstripe:${short_hash}"

  if [ $git_branch == 'calm' ]; then
    tags="-t 864879987165.dkr.ecr.us-east-1.amazonaws.com/calm/localstripe:latest ${tags}"
  fi

  echo "Building container"
  echo docker build ${tags} .
}

cmd_integ() {
  docker build -t calm_localstripe:test .
  docker run -d --rm calm_localstripe:test
  timeout=5; while [ $((timeout--)) -ge 0 ]; do
    nc -z -w 1 localhost 8420; r=$?; [ $r -eq 0 ] && break; sleep 1;
  done;
  ./test.sh
  echo "INTEG PASSED"
}

main() {
  case "$1" in
    build)
      cmd_build ${@:2};;
    integ)
      cmd_integ ${@:2};;
    *)
      help; exit 1
  esac
}

main "$@"
