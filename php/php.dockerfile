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

COPY ./spx.ini /usr/local/etc/php/conf.d/spx.ini

RUN docker-php-ext-enable spx

RUN docker-php-ext-install pdo pdo_mysql

# Enable FPM status page
RUN echo "pm.status_path = /status" >> /usr/local/etc/php-fpm.d/www.conf
RUN echo "process.dumpable = yes" >> /usr/local/etc/php-fpm.d/www.conf

# Install APCu for caching (for prometheus client)
RUN pecl install apcu \
    && docker-php-ext-enable apcu
