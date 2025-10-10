# CI/CD Pipeline Documentation

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Multi-Tenant SaaS Backend. The pipeline is implemented using **GitHub Actions** and automates testing, linting, building, and deployment processes.

## Pipeline Architecture

### Workflow File

Location: `.github/workflows/backend.yml`

### Trigger Events

The pipeline runs on:
- **Push** to `main` or `develop` branches
- **Pull Requests** targeting `main` or `develop` branches

## Pipeline Stages

### 1. Lint & Format Check

**Purpose**: Ensure code quality and consistent formatting

**Steps**:
- Set up Python 3.11
- Cache pip dependencies for faster builds
- Install linting tools (pycodestyle, black, flake8)
- Run pycodestyle (PEP 8 compliance)
- Run flake8 (additional linting)
- Check code formatting with black

**Exit Criteria**: All linting checks must pass

### 2. Test Suite

**Purpose**: Validate application functionality and prevent regressions

**Services**:
- **PostgreSQL 14**: Database service for integration tests
- **Redis 7**: Caching and rate limiting backend

**Steps**:
- Set up Python 3.11
- Cache pip dependencies
- Install project dependencies
- Create `.env` file with test configuration
- Run Alembic migrations check
- Execute pytest test suite (138+ tests)

**Environment Variables**:
- `DATABASE_URL`: SQLite for unit tests
- `REDIS_URL`: Redis connection for caching tests
- `SECRET_KEY`: Test JWT secret
- `PROJECT_NAME`: Application name

**Exit Criteria**: All tests must pass

### 3. Docker Build & Push

**Purpose**: Build and publish Docker image to GitHub Container Registry

**Conditions**:
- Only runs after lint and test stages pass
- Only on push to `main` branch

**Steps**:
- Set up Docker Buildx
- Log in to GitHub Container Registry (ghcr.io)
- Extract metadata (tags, labels)
- Build multi-stage Docker image
- Push to registry with appropriate tags

**Image Tags**:
- `latest`: Most recent main branch build
- `main-<sha>`: Build from specific commit
- `main`: Latest main branch build

**Registry**: `ghcr.io/<username>/multi-tenant-saas-backend`

## Configuration Files

### .flake8

Linting configuration for flake8:
- Max line length: 88 characters (black compatible)
- Excludes: migrations, cache, build artifacts
- Ignores: E203, W503, E501 (compatibility with black)

### .editorconfig

Editor configuration for consistent formatting:
- Charset: UTF-8
- End of line: LF
- Python indent: 4 spaces
- YAML indent: 2 spaces
- Max line length: 88

### Dockerfile

Multi-stage Docker build:
- Builder stage: Install dependencies
- Final stage: Minimal runtime image
- Health check: `/health` endpoint
- Port: 8000

## Environment Variables & Secrets

### Required GitHub Secrets

For Docker push (automatically available):
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Future Deployment Secrets (Optional)

If deploying to cloud platforms:
- `DOCKERHUB_TOKEN`: Docker Hub authentication
- `DEPLOY_KEY`: SSH key for deployment
- `SENTRY_DSN`: Error monitoring
- `DATABASE_URL`: Production database
- `REDIS_URL`: Production Redis

## Usage

### Viewing Pipeline Status

1. Go to repository **Actions** tab
2. View recent workflow runs
3. Click on a run to see detailed logs

### Adding Status Badge to README

```markdown
![CI/CD Pipeline](https://github.com/<username>/multi-tenant-saas-backend/workflows/Backend%20CI%2FCD%20Pipeline/badge.svg)
```

### Running Locally

To replicate CI/CD checks locally:

```bash
# Linting
pycodestyle app/ --count --statistics --max-line-length=88
flake8 app/ --count --statistics
black --check app/

# Testing
pytest tests/ -v

# Docker build
docker build -t multi-tenant-saas:local .
docker run -p 8000:8000 multi-tenant-saas:local
```

## Optimization Features

### Caching

- **pip dependencies**: Cached using `actions/cache@v4`
- **Docker layers**: Cached using GitHub Actions cache

### Parallel Jobs

- Lint and Test jobs run in parallel
- Build job depends on successful completion of both

### Fast Failure

- `--maxfail=5` in pytest: Stop after 5 failures
- Early exit on linting errors

## Troubleshooting

### Common Issues

1. **Linting Failures**
   - Fix: Run `black app/` locally to auto-format
   - Fix: Review pycodestyle output and fix violations

2. **Test Failures**
   - Check service availability (PostgreSQL, Redis)
   - Verify environment variables in `.env`
   - Review test logs in Actions tab

3. **Docker Build Failures**
   - Verify Dockerfile syntax
   - Check if all required files are present
   - Ensure requirements.txt is up to date

### Debug Mode

Enable debug logging in workflow:

```yaml
- name: Debug step
  run: |
    echo "Runner OS: ${{ runner.os }}"
    echo "Python version: ${{ env.PYTHON_VERSION }}"
    env
```

## Best Practices

1. **Keep workflows fast**: Use caching and parallel jobs
2. **Fail fast**: Exit early on critical errors
3. **Clear error messages**: Provide context in step names
4. **Security**: Never commit secrets to code
5. **Version pinning**: Use specific action versions (v4, v5)

## Integration with Development Workflow

### Pull Request Flow

1. Developer creates feature branch
2. Opens pull request to `develop`
3. CI/CD pipeline runs automatically
4. All checks must pass before merge
5. Reviewers can see test results

### Release Flow

1. Merge `develop` to `main`
2. CI/CD pipeline runs
3. Docker image built and pushed
4. Optional: Auto-deploy to staging
5. Manual promotion to production

## Future Enhancements

- [ ] Auto-deployment to staging environment (Render/Railway)
- [ ] Performance benchmarking in CI
- [ ] Security scanning (Snyk, Trivy)
- [ ] Code coverage reports (codecov.io)
- [ ] Automatic changelog generation
- [ ] Slack/Discord notifications
- [ ] Blue-green deployment strategy

## Monitoring

### Pipeline Metrics

Track:
- Build duration
- Test execution time
- Success/failure rate
- Docker image size

### Alerts

Set up GitHub Actions notifications for:
- Failed builds on `main`
- Consistently failing tests
- Dependency vulnerabilities

## Maintenance

### Regular Tasks

- Update GitHub Actions versions quarterly
- Review and update Python dependencies monthly
- Prune old Docker images from registry
- Audit and rotate secrets annually

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Last Updated**: Phase 4 - Sprint 4.1  
**Pipeline Version**: 1.0.0  
**Status**: ✅ Active
