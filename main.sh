#!/usr/bin/env bash

set -e

cmd_build() {
  short_hash=$(git rev-parse --short HEAD)

  echo "Building container"
  docker build \
      -t 864879987165.dkr.ecr.us-east-1.amazonaws.com/calm/localstripe:latest \
      -t 864879987165.dkr.ecr.us-east-1.amazonaws.com/calm/localstripe:${short_hash} .
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
