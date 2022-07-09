#!/usr/bin/env bash
docker run --rm -v=$(pwd)/output:/srv/output -v=$(pwd)/pipeline:/srv/pipeline:ro -w=/srv heartbot-pipeline:latest python pipeline