FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y software-properties-common curl \
	&& add-apt-repository -y ppa:deadsnakes/ppa \
	&& apt-get install -y \
	python3.12 python3.12-venv \
	git clang-15 \
	build-essential cmake meson ninja-build \
	libssl-dev libnuma-dev pkg-config libcurl4-openssl-dev \
	libbpf-dev m4 libpcap-dev libsqlite3-dev \
	protobuf-compiler libprotobuf-dev \
	libdpdk-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN python3.12 -m ensurepip --upgrade && \
	python3.12 -m pip install --upgrade pip setuptools wheel && \
	update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
	update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

COPY install_oclint.sh /tmp/install_oclint.sh
RUN chmod +x /tmp/install_oclint.sh && /tmp/install_oclint.sh

RUN python3 -m pip install --no-cache-dir pyelftools

RUN curl -sL https://github.com/jupp0r/prometheus-cpp/archive/refs/tags/v1.2.4.tar.gz | tar -xz \
	&& mkdir -p /usr/local/include/prometheus/detail \
	&& cp -r prometheus-cpp-1.2.4/core/include/prometheus/. /usr/local/include/prometheus/ \
	&& cp -r prometheus-cpp-1.2.4/push/include/prometheus/. /usr/local/include/prometheus/ \
	&& printf '#ifndef PROMETHEUS_CPP_CORE_EXPORT_H\n#define PROMETHEUS_CPP_CORE_EXPORT_H\n#define PROMETHEUS_CPP_CORE_EXPORT\n#endif\n' > /usr/local/include/prometheus/detail/core_export.h \
	&& printf '#ifndef PROMETHEUS_CPP_PUSH_EXPORT_H\n#define PROMETHEUS_CPP_PUSH_EXPORT_H\n#define PROMETHEUS_CPP_PUSH_EXPORT\n#endif\n' > /usr/local/include/prometheus/detail/push_export.h \
	&& printf '#ifndef PROMETHEUS_CPP_PULL_EXPORT_H\n#define PROMETHEUS_CPP_PULL_EXPORT_H\n#define PROMETHEUS_CPP_PULL_EXPORT\n#endif\n' > /usr/local/include/prometheus/detail/pull_export.h \
	&& cp -r prometheus-cpp-1.2.4/pull/include/prometheus/. /usr/local/include/prometheus/ \
	&& rm -rf prometheus-cpp-1.2.4

WORKDIR /app

ENV PATH="/opt/oclint/bin:${PATH}"

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENTRYPOINT ["python", "-m", "src.main"]