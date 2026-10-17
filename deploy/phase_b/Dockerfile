# Already-local Phase A image; immutable source includes cryptography 50.0.1.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /app
COPY common /app/common
COPY gateway /app/gateway
COPY cloud /app/cloud
COPY device /app/device
COPY deploy/phase_b/tls-policy.cnf /run/pqc/tls-policy.cnf
ENV OPENSSL_CONF=/run/pqc/tls-policy.cnf PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "common.secure_bootstrap"]
