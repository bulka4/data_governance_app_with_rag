# Script which builds Docker images and loads them to kind. Run it on a local machine (not in the Docker container for interacting with kind)

# Build and load the image for preparaing the model for the semantic search service
docker build -t semantic-search -f services/semantic_search/Dockerfile services/semantic_search

kind load docker-image semantic-search --name data-gov

# Build and load the image for metadata extraction and data governance backed (running Node.js)
docker build -t nodejs -f dockerfiles/nodejs.Dockerfile dockerfiles

kind load docker-image nodejs --name data-gov