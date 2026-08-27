FROM ubuntu:22.04

# ========== Define build-time variables ==========

# Names of images we will build and load to kind which will be used when deploying resources on kind. Those are images for:
# - Airflow
ARG CLUSTER_NAME=data-gov
ARG AIRFLOW_IMAGE_NAME=airflow:latest
# This prevents prompting user for input for example when using apt-get.
ENV DEBIAN_FRONTEND=noninteractive


# Tell Docker to use bash for the rest of the Dockerfile
SHELL ["/bin/bash", "-c"]

WORKDIR /root




# ============ Install Helm and kubectl =============

# Install Helm
RUN apt-get update && \
    apt-get -y install curl && \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash


# Install kubectl for interacting with a kind cluster
RUN apt-get install -y apt-transport-https ca-certificates gnupg && \
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \

    # Add the GPG key and APT repository URL to the kubernetes.list. That url will be used to pull Kubernetes packages (like kubectl)
    <<EOF cat >> /etc/apt/sources.list.d/kubernetes.list
deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /
EOF

RUN apt-get update && \
    apt-get install -y kubectl && \
    apt-mark hold kubectl




# ============ Update kubeconfig file (.kube/config) ============

# Copy the kubeconfig file from the host
COPY .kube /root/.kube

# Update the kubeconfig file (.kube/config) to specify IP of the Kubernetes cluster to use:
#   - host.docker.internal is the DNS name mapped to the IP of the host where this image will be running (created automatically by Docker)
#   - 6443 is the port on which cluster is listening. We specified that port in the kind-config file
RUN kubectl config set-cluster kind-$CLUSTER_NAME \
    --server=https://host.docker.internal:6443 \
    --insecure-skip-tls-verify=true




# ========== Install other useful tools =============
# Install: nano
RUN apt-get install nano




# ============ Create and save a bash script for building images and loading them to kind =============

# Those images will be used for deploying different parts of the system as pods. Those are images for:
# - Airflow

# Copy Dockerfiles and other files needed for building images
COPY dockerfiles /root/dockerfiles

# Save the script for building images and loading them to kind.
RUN <<EOF cat > /root/dockerfiles/build_and_load.sh
docker build -t $AIRFLOW_IMAGE_NAME -f dockerfiles/airflow.Dockerfile dockerfiles

kind load docker-image $AIRFLOW_IMAGE_NAME --name $CLUSTER_NAME
EOF

RUN \
    # Remove the '\r' sign from the script
    sed -i 's/\r$//' /root/dockerfiles/build_and_load.sh && \
    # Make the script executable
    chmod +x /root/dockerfiles/build_and_load.sh




# ============ Copy other needed folders ==============

# Helm charts for deploying all the resources
COPY helm_charts /root/helm_charts
# Script for creating Kubernetes namespaces and secrets
COPY bash/create_k8s_secrets.sh /root/bash/create_k8s_secrets.sh
# Kubernetes YAML manifests
COPY k8s /root/k8s





# Run the script for building and pushing images to ACR and start a bash session
# CMD ["bash", "-c", "/root/dockerfiles/build_and_load.sh && /bin/bash"]