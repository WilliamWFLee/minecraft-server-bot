#!/bin/bash

. .env
tmux new-session -d -s $SESSION_NAME
poetry run -- python main.py
