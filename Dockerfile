FROM --platform=linux/amd64 sagemath/sagemath@sha256:e068670ae5863b54b2550e72437ec637b0283acb0dc712c8584c124dbf44e667

USER 0

# The upstream image declares USER sage, but recent builds do not include
# matching passwd/group entries. Add the minimal users Docker/VS Code need.
RUN printf 'root:x:0:0:root:/root:/bin/bash\nsage:x:1001:1001:Sage:/home/sage:/bin/bash\n' > /etc/passwd \
 && printf 'root:x:0:\nsage:x:1001:\n' > /etc/group \
 && mkdir -p /root /home/sage/.sage /home/sage/.local \
 && chown -R 1001:1001 /home/sage/.sage /home/sage/.local

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3-pip \
 && rm -rf /var/lib/apt/lists/*

# Install Jupyter + ipykernel into Sage's Python environment
RUN sage -pip install --no-cache-dir jupyter jupyterlab ipykernel

# Install kernels for the *sage user* (no /usr/local permission issues)
USER sage
ENV HOME=/home/sage
ENV SAGE_DOT_SAGE=/home/sage/.sage

RUN sage -python -m ipykernel install --user --name sagemath --display-name "SageMath" \
 && sage -python -m ipykernel install --user --name sage-python --display-name "Python (Sage env)" \
 && /usr/bin/python3 -m pip install ipykernel -U --user --force-reinstall --break-system-packages \
 && /usr/bin/python3 -m ipykernel install --user --name python312 --display-name "Python 3.12.3" \
 && sage -python -m jupyter kernelspec list

WORKDIR /home/sage/work
