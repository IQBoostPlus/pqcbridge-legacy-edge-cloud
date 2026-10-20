# Offline rebuild from the A/B validated immutable OpenSSL 3.5 image.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /app
COPY common /app/common
COPY gateway /app/gateway
COPY cloud /app/cloud
COPY device /app/device
COPY scripts/phase_d/worker.py /app/pilot_worker.py
COPY deploy/phase_b/tls-policy.cnf /run/pqc/tls-policy.cnf
ENV OPENSSL_CONF=/run/pqc/tls-policy.cnf PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ARG PACKAGE_VERSION=pilot-lab-v1
LABEL org.pqcbridge.package=${PACKAGE_VERSION}
ENTRYPOINT ["python", "-m", "common.managed_bootstrap"]
