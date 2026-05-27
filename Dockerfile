FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
	software-properties-common=0.99.22.9 \
	curl=7.81.0-1ubuntu1.24 \
	&& add-apt-repository -y ppa:deadsnakes/ppa \
	&& apt-get install -y \
	python3.12=3.12.13-1+jammy1 \
	python3.12-venv=3.12.13-1+jammy1 \
	git=1:2.34.1-1ubuntu1.17 \
	clang-15=1:15.0.7-0ubuntu0.22.04.3 \
	build-essential=12.9ubuntu3 \
	cmake=3.22.1-1ubuntu1.22.04.2 \
	meson=0.61.2-1 \
	ninja-build=1.10.1-1 \
	libssl-dev=3.0.2-0ubuntu1.23 \
	libnuma-dev=2.0.14-3ubuntu2 \
	pkg-config=0.29.2-1ubuntu3 \
	libcurl4-openssl-dev=7.81.0-1ubuntu1.24 \
	libbpf-dev=1:0.5.0-1ubuntu22.04.1 \
	m4=1.4.18-5ubuntu2 \
	libpcap-dev=1.10.1-4build1 \
	libsqlite3-dev=3.37.2-2ubuntu0.5 \
	protobuf-compiler=3.12.4-1ubuntu7.22.04.6 \
	libprotobuf-dev=3.12.4-1ubuntu7.22.04.6 \
	libdpdk-dev=21.11.9-0ubuntu0.22.04.2 \
	&& rm -rf /var/lib/apt/lists/*

RUN python3.12 -m ensurepip --upgrade && \
	python3.12 -m pip install --no-cache-dir pip==26.1.1 setuptools==82.0.1 wheel==0.47.0 && \
	update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
	update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

COPY install_oclint.sh /tmp/install_oclint.sh
RUN chmod +x /tmp/install_oclint.sh && /tmp/install_oclint.sh

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