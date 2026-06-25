FROM sagemath/sagemath:latest

USER root

# Essentials + ensure `python` exists (VS Code/Jupyter sometimes spawns `python`)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates tar gzip xz-utils \
    python3 python3-pip python-is-python3 \
 && rm -rf /var/lib/apt/lists/*

# Install Jupyter + ipykernel into Sage's Python environment
RUN sage -pip install --no-cache-dir jupyter jupyterlab ipykernel

# Create writable Sage home dirs and fix ownership (prevents IPython temp-dir warning)
RUN mkdir -p /home/sage/.sage /home/sage/.local \
 && chown -R sage:sage /home/sage

# Install kernels for the *sage user* (no /usr/local permission issues)
USER sage
ENV HOME=/home/sage
ENV SAGE_DOT_SAGE=/home/sage/.sage

RUN sage -python -m ipykernel install --user --name sagemath --display-name "SageMath" \
 && sage -python -m ipykernel install --user --name sage-python --display-name "Python (Sage env)" \
 && sage -python -m jupyter kernelspec list

WORKDIR /home/sage/work
