# Multi-stage build for C# .NET 8 Payment Service
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

# Copy project file and restore dependencies
COPY payment-service.csproj .
RUN dotnet restore

# Copy source code and publish release build
COPY . .
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0-alpine AS runtime

WORKDIR /app

RUN apk upgrade --no-cache

# Run as non-root user built into .NET 8 images
USER $APP_UID

COPY --from=build /app/publish .

EXPOSE 8085

ENTRYPOINT ["dotnet", "payment-service.dll"]
