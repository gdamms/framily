#!/bin/bash

# curl localhost:8000/api/v1/framily/create with post data with the following json:
# {
#   "name": "test framily",
# }
curl -X POST localhost:8000/api/v1/framily/create \
  -H "Content-Type: application/json" \
  -d '{"name": "test framily"}' >> test_framily_create_response.tmp.json
