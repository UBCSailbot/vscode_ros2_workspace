# Copied from https://github.com/microsoft/vscode-dev-containers/blob/5a084a93b0736ea86395ac99019a5b72a00b6341/containers/javascript-node-mongo/.devcontainer/Dockerfile
# [Choice] Node.js version (use -bullseye variants on local arm64/Apple Silicon): 18, 16, 14, 18-bullseye, 16-bullseye, 14-bullseye, 18-buster, 16-buster, 14-buster
ARG VARIANT=18
FROM mcr.microsoft.com/vscode/devcontainers/javascript-node:0-${VARIANT}

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] Uncomment if you want to install an additional version of node using nvm
# ARG EXTRA_NODE_VERSION=10
# RUN su node -c "source /usr/local/share/nvm/nvm.sh && nvm install ${EXTRA_NODE_VERSION}"

# [Optional] Uncomment if you want to install more global node modules
# RUN su node -c "npm install -g <your-package-list-here>"

# Adapted from https://www.digitalocean.com/community/tutorials/how-to-build-a-node-js-application-with-docker
WORKDIR /website
EXPOSE 3005
CMD npm install --legacy-peer-deps && npm run dev
