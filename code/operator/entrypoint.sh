#!/bin/sh
# WATCH_NAMESPACE: if set, watch only this namespace; otherwise watch all namespaces.
set -e
if [ -n "$WATCH_NAMESPACE" ]; then
  exec kopf run --standalone --namespace="$WATCH_NAMESPACE" operator/main.py "$@"
else
  exec kopf run --standalone --all-namespaces operator/main.py "$@"
fi
