# Ruby Sinatra Notification Service
FROM ruby:3.3-alpine3.24

WORKDIR /app

# Install native dependencies for PostgreSQL and build the required gems.
RUN apk upgrade --no-cache \
    && apk add --no-cache postgresql-libs \
    && apk add --no-cache --virtual .build-deps build-base postgresql-dev

# Install gems
COPY Gemfile Gemfile.lock ./
RUN bundle install \
    && apk del .build-deps \
    && rm -rf \
        /usr/local/lib/ruby/gems/3.3.0/specifications/default/resolv-0.3.1.gemspec \
        /usr/local/lib/ruby/gems/3.3.0/gems/resolv-0.3.1

# Copy application source
COPY . .

# Run as non-root user
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8086

CMD ["bundle", "exec", "ruby", "app.rb"]
