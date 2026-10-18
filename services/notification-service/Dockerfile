# Ruby Sinatra Notification Service
FROM ruby:3.3-alpine3.24

WORKDIR /app

# Install native dependencies for PostgreSQL and build the required gems.
RUN apk upgrade --no-cache \
    && apk add --no-cache postgresql-libs \
    && apk add --no-cache --virtual .build-deps build-base postgresql-dev

# Install gems
COPY Gemfile Gemfile.lock ./
RUN bundle install && apk del .build-deps

# Copy application source
COPY . .

# Run as non-root user
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8086

CMD ["bundle", "exec", "ruby", "app.rb"]
