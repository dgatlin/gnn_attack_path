# Development Guide

## Feature Branch Workflow

This project follows a feature branch workflow for development and CI/CD.

### Branch Naming Convention

- **Feature branches**: `feature/description-of-feature`
- **Bug fixes**: `fix/description-of-bug`
- **Hotfixes**: `hotfix/description-of-hotfix`
- **Release branches**: `release/version-number`

### Getting Started

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

4. **Push to remote**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Go to GitHub and create a PR
   - Add reviewers
   - Link any related issues

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Frontend Development

#### Prerequisites
- Node.js 18+
- npm or yarn

#### Setup
```bash
cd ui
npm install
npm start
```

#### Available Scripts
- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run lint` - Run ESLint

#### Testing
```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- --testPathPattern=AttackPathAnalysis
```

### Backend Development

#### Prerequisites
- Python 3.9+
- pip

#### Setup
```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

#### Testing
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test module
pytest tests/unit/test_api_endpoints.py -v
```

### CI/CD Pipeline

#### Frontend Pipeline
- **Trigger**: Push to any branch with `ui/` changes
- **Steps**:
  1. Install dependencies
  2. Run linting
  3. Build application
  4. Run tests
  5. Upload build artifacts

#### Backend Pipeline
- **Trigger**: Push to any branch with backend changes
- **Steps**:
  1. Install Python dependencies
  2. Run backend tests
  3. Generate coverage reports
  4. Upload to codecov

#### Integration Pipeline
- **Trigger**: After frontend and backend pipelines pass
- **Steps**:
  1. Start backend server
  2. Build and start frontend
  3. Run integration tests
  4. Verify both services are running

### Code Quality Standards

#### Frontend
- Use TypeScript for type safety
- Follow React best practices
- Use Tailwind CSS for styling
- Write unit tests for components
- Use ESLint for code quality

#### Backend
- Follow PEP 8 style guide
- Use type hints
- Write comprehensive tests
- Use async/await for async operations
- Document API endpoints

### Testing Strategy

#### Unit Tests
- Test individual components/functions
- Mock external dependencies
- Aim for high coverage (>80%)

#### Integration Tests
- Test component interactions
- Test API endpoints
- Test database operations

#### End-to-End Tests
- Test complete user workflows
- Test cross-service communication
- Test in production-like environment

### Pull Request Process

1. **Create PR** from feature branch to main
2. **Add reviewers** - at least 2 reviewers
3. **Run CI/CD** - all checks must pass
4. **Code review** - address feedback
5. **Merge** - squash and merge to main
6. **Delete branch** - clean up feature branch

### Deployment

#### Development
- Feature branches deploy to preview environments
- Automatic deployment on PR creation

#### Production
- Main branch deploys to production
- Requires manual approval
- Rollback capability available

### Troubleshooting

#### Common Issues

**Frontend won't start**:
```bash
cd ui
rm -rf node_modules package-lock.json
npm install
npm start
```

**Backend tests failing**:
```bash
pip install -r requirements.txt
pytest tests/ -v --tb=short
```

**Docker issues**:
```bash
docker-compose down
docker-compose up --build
```

### Resources

- [React Documentation](https://reactjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
