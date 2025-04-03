#! /bin/bash

docker stop qdrant
docker rm qdrant
docker run -d -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant