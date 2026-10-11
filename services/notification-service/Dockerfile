# Ruby Sinatra Notification Service
FROM ruby:3.3-slim

WORKDIR /app

# Install native dependencies required by PostgreSQL and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install gems
COPY Gemfile Gemfile.lock ./
RUN bundle install

# Copy application source
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8086

CMD ["bundle", "exec", "ruby", "app.rb"]
