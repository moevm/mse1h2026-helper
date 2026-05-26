FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
	build-essential \
	git \
	python-is-python3 \
	python3-pip \
	wget \
	clang-15 \
	apt-file && \
	ln -sf /usr/bin/clang-15 /usr/bin/clang && \
	ln -sf /usr/bin/clang++-15 /usr/bin/clang++ && \
	apt-file update

COPY install_oclint.sh /tmp/install_oclint.sh
RUN chmod +x /tmp/install_oclint.sh && /tmp/install_oclint.sh

WORKDIR /app

ENV PATH="/opt/oclint/bin:${PATH}"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENTRYPOINT ["python", "-m", "src.main"]