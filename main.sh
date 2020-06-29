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
  docker build ${tags} .
}

cmd_integ() {
  docker stop calm_localstripe_test || echo 'no'
  docker build -t calm_localstripe:test .
  docker run -d --rm --name calm_localstripe_test calm_localstripe:test
  sleep 5
  r=0
  docker exec -i calm_localstripe_test ./test.sh || r=$?
  docker stop calm_localstripe_test
  docker rmi calm_localstripe:test
  [ $r -ne 0 ] && echo 'Tests failed' && exit $r
  echo "INTEG PASSED"
}

cmd_local_setup() {
  python3 -m venv .venv
  source .venv/bin/activate
  pip3 install -r requirements.txt
  if ! which entr 2>/dev/null ; then
    echo '"entr" not installed. Install it with "brew install entr"'
    exit 1
  fi
}

cmd_local_dev() {
  if ! source .venv/bin/activate ; then
    echo "virtual env not setup. run local_setup first" >&2
    exit 1
  fi
  find . -name '*.py' | entr -r python3 -m localstripe --from-scratch --port 8421
}

main() {
  case "$1" in
    build)
      cmd_build "${@:2}";;
    integ)
      cmd_integ "${@:2}";;
    local_setup)
      cmd_local_setup "${@:2}";;
    local_dev)
      cmd_local_dev "${@:2}";;
    *)
      help; exit 1
  esac
}

main "$@"
