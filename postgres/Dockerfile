FROM postgres:15

# Install required dependencies: Git, GCC, Make, and PostgreSQL server development libraries
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    make \
    postgresql-server-dev-15 \
    && git clone https://github.com/pgvector/pgvector.git \
    && cd pgvector && make && make install \
    && apt-get remove -y git gcc make postgresql-server-dev-15 \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /pgvector
