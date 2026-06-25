# Isolated Python execution sandbox (Week 3)
FROM python:3.12-slim-bookworm

RUN useradd --create-home --shell /bin/bash sandbox \
    && pip install --no-cache-dir --disable-pip-version-check \
       restrictedpython==8.0

WORKDIR /home/sandbox
USER sandbox

COPY --chown=sandbox:sandbox run_code.py /home/sandbox/run_code.py

ENTRYPOINT ["python", "/home/sandbox/run_code.py"]
