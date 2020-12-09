# Multi-arch docker-compose image
FROM registry.gitlab.com/ix.ai/docker-compose:1.27.4
LABEL maintainer="docker@ix.ai"\
      ai.ix.repository="ix.ai/swarm-launcher"

RUN apk add --no-cache bash curl jq

# add entrypoint.sh launcher script
ADD entrypoint.sh /

# run the image
ENTRYPOINT /entrypoint.sh
