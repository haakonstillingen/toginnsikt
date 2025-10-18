# Toginnsikt - Train Delay Monitoring System

A comprehensive train delay monitoring system for the L2 line between Myrvoll and Oslo S, built with Python backend and Next.js dashboard.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL database
- Google Cloud Platform account (for production)

### Local Development
```bash
# Clone the repository
git clone https://github.com/haakonstillingen/toginnsikt.git
cd toginnsikt

# Install Python dependencies
pip install -r requirements.txt

# Install dashboard dependencies
cd toginnsikt-dashboard
npm install

# Start the dashboard
npm run dev
```

### Production Deployment
```bash
# Deploy to Google Cloud Run
./deploy.sh
```

## 📊 System Overview

Toginnsikt collects real-time train delay data from the Entur API and provides insights through a web dashboard.

### Architecture
```
Entur API → Enhanced Collector → Cloud SQL → Next.js API → Frontend Dashboard
```

### Key Features
- **Real-time Data Collection**: Automated collection every 15 minutes
- **Route Validation**: Prevents incorrect destination collection
- **Delay Analysis**: Comprehensive delay tracking and classification
- **Interactive Dashboard**: Real-time visualization of delay patterns
- **Two-Tier Collection**: Planned departures + actual departures

## 📁 Project Structure

```
toginnsikt/
├── enhanced_commute_collector_cloud.py  # Main data collector
├── collection_scheduler.py              # Collection scheduling
├── config_cloud.py                      # Configuration
├── migration_*.py                       # Database migrations
├── toginnsikt-dashboard/                # Next.js frontend
├── docs/                                # Documentation
│   ├── architecture/                    # System design docs
│   ├── testing/                         # Testing guidelines
│   ├── deployment/                      # Deployment docs
│   └── development/                     # Development docs
├── debug_and_test_scripts/              # Test and debug scripts
└── migrations/                          # Database schema changes
```

## 🧪 Testing

The project follows Test-Driven Development (TDD) practices:

```bash
# Run tests
cd debug_and_test_scripts
python test_route_validation_simple.py

# Run all route validation tests
python run_route_validation_tests.py
```

See `docs/testing/TDD_GUIDELINES.md` for detailed testing practices.

## 📚 Documentation

- **System Design**: `docs/architecture/collection_strategy.md`
- **Testing Guidelines**: `docs/testing/TDD_GUIDELINES.md`
- **Deployment Guide**: `docs/deployment/MIGRATION_SYSTEM.md`
- **Development Status**: `docs/development/todo.md`

## 🔧 Configuration

### Environment Variables
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password

### Cloud Configuration
- Google Cloud SQL for database
- Google Cloud Run for deployment
- Google Secret Manager for credentials

## 🚂 Data Collection

### Routes Monitored
- **Morning Commute**: Myrvoll → Oslo S (Lysaker/Stabekk destinations)
- **Afternoon Commute**: Oslo S → Myrvoll (Ski destination)

### Collection Schedule
- **Planned Departures**: Daily at 03:00 UTC
- **Actual Departures**: Every 15 minutes (adaptive scheduling)
- **Rush Hours**: 15-minute intervals (06:00-09:00, 15:00-18:00 UTC)
- **Regular Hours**: 30-minute intervals
- **Night Hours**: 60-minute intervals

## 📈 Dashboard Features

- Real-time delay visualization
- Route filtering (Morning/Afternoon)
- Time period selection
- Delay percentage tracking
- Historical data analysis

Access the dashboard at: http://localhost:3000 (development)

## 🛠️ Development

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Implement TDD practices
- Follow conventional commit format

### Git Workflow
- Use feature branches
- All PRs must reference issues
- Follow separation of concerns
- Write tests before implementation

See `.cursorrules` for detailed development guidelines.

## 📊 Current Status

- ✅ **Data Collection**: Active and collecting real-time data
- ✅ **Route Validation**: Prevents incorrect data collection
- ✅ **Dashboard**: Live and displaying delay patterns
- ✅ **Testing**: Comprehensive test suite with TDD practices
- ✅ **Documentation**: Complete and organized

## 🤝 Contributing

1. Read the documentation in `docs/`
2. Follow TDD practices (see `docs/testing/TDD_GUIDELINES.md`)
3. Write tests before implementation
4. Follow the git workflow guidelines
5. Update documentation when making changes

## 📄 License

This project is for monitoring train delays on the L2 line in Norway.

## 🔗 Links

- **Dashboard**: http://localhost:3000 (development)
- **API**: https://togforsinkelse-collector-383318038289.europe-north1.run.app
- **Documentation**: `docs/README.md`
- **Test Scripts**: `debug_and_test_scripts/README.md`
