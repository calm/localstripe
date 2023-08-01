#!/usr/bin/env bash

set -e
if [[ -z "${short_hash+1}" ]] ; then
  short_hash=$(git rev-parse HEAD | cut -c1-8 )
  echo "short_hash is not set; use the first 8 characters of the latest git hash ${short_hash}"
fi

base_image='864879987165.dkr.ecr.us-east-1.amazonaws.com/calm/localstripe'

cmd_build() {
  git_branch=$(git rev-parse --abbrev-ref HEAD)
  tags="-t ${base_image}:${short_hash}"

  if [ "$git_branch" == 'calm' ]; then
    tags="-t ${base_image}:latest ${tags}"
  fi

  echo "################### Creating multi-platform builder ###################"
  docker buildx create --use --platform=linux/arm64,linux/amd64 --name multi-platform-builder

  echo "################### Building multi-platform image ###################"
  # shellcheck disable=SC2086
  docker buildx build --push --platform linux/amd64,linux/arm64 ${tags} .

  # building individual images for each platform with separate tags
  for plat in amd64 arm64 ; do
    echo "################### Building $plat image ###################"
    tag="${base_image}:${short_hash}-${plat}"
    echo "# Using tag: $tag"
    docker buildx build --push --platform "linux/${plat}" -t "$tag" .
  done

}

cmd_integ() {
  docker stop calm_localstripe_test || echo 'no'
  docker build -t calm_localstripe:test . --build-arg seed_dir='fixtures/integration_test'
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
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip3 install -r requirements.txt
  if ! which entr 2>/dev/null ; then
    brew install entr
  fi
}

cmd_local_dev() {
  # shellcheck disable=SC1091
  if ! source .venv/bin/activate ; then
    echo "virtual env not setup. run local_setup first" >&2
    exit 1
  fi
  find . -name '*.py' -a -not -path './*venv/*' | entr -r python3 -m localstripe --from-scratch --port 8421
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
