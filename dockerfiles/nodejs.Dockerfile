# An image for using Node.js (running the data governance backend and metadata extraction pipeline)

FROM node:22-bookworm-slim

WORKDIR /app

# COPY services/metadata_extraction/ ./

# # Install nodejs dependencies from the package.json
# RUN cd /app/services/metadata_extraction && \
#     npm init -y && \
#     npm install