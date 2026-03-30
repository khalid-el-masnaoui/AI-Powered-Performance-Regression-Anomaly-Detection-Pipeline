FROM php:8.2-fpm

# install extensions and other dependencies
RUN apt-get update && apt-get install -y \
    zlib1g-dev \
    libpq-dev \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libmemcached-dev \
    curl \
    vim \
    git \
    zip \
    unzip \
    graphviz


WORKDIR /var/www
 
# Install SPX
RUN git clone https://github.com/NoiseByNorthwest/php-spx.git /tmp/php-spx \
    && cd /tmp/php-spx \
    && phpize \
    && ./configure \
    && make \
    && make install

# Install Redis extension
RUN pecl install redis && docker-php-ext-enable redis
