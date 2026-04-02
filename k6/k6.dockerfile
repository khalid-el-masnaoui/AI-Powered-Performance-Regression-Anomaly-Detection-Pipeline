# Use the official k6 image as a base
FROM grafana/k6:latest

# Switch to root to install packages
USER root

# Install bash, curl and jq
RUN apk update && \
    apk add --no-cache bash && \
    apk add --no-cache curl &&  \
    apk add --no-cache jq

# Switch back to the k6 user for security
#USER k6

# Set bash as our entrypoint
ENTRYPOINT ["/bin/bash", "-c"]
