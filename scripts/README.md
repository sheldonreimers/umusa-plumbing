# 🔧 Umusa Plumbing - Data Analytics & Automation Scripts

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **⚠️ PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**
> 
> This repository contains proprietary business logic and automation scripts developed exclusively for Umusa Plumbing. Unauthorized use, reproduction, or distribution is strictly prohibited.

---

## 📋 Overview

This repository houses the complete data analytics and automation infrastructure for Umusa Plumbing's operations, including:

- **Field Service Management Integration** (ServiceM8)
- **Inventory & Stock Management Automation**
- **Customer Relationship Management (CRM) Integration**
- **Data Warehousing & Analytics Pipelines**
- **Automated Reporting & Notifications**
- **Business Intelligence Dashboards**

### 🏗️ Architecture

```
scripts/
├── services/              # Reusable API service wrappers
│   ├── ServiceM8.py      # Field service management
│   ├── GoogleSheets.py   # Spreadsheet automation
│   ├── GoogleBigQuery.py # Data warehouse integration
│   ├── Intercom.py       # Customer communication
│   ├── HubspotAPI.py     # CRM integration
│   └── SecretManager.py  # Credentials & secrets management
│
├── src/                   # Modular automation scripts
│   ├── stock_manager/    # Inventory tracking automation
│   └── script_template/  # Reusable script architecture template
│
└── linter/               # Code quality & naming validation

```

---

## 🚀 Key Modules

### Stock Manager (`src/stock_manager/`)
Automated daily inventory tracking from ServiceM8 field forms to Google Sheets with weekly aggregation and reporting.

**Features:**
- Real-time inventory data collection
- Staff-level tracking and attribution
- Automated weekly consolidation
- Historical data preservation
- Environment-aware deployment (Staging/Production)

### Services Layer (`services/`)
Centralized API clients and integrations for:
- **ServiceM8** - Field service management platform
- **Google Cloud** - Sheets, BigQuery, Drive
- **CRM Systems** - Intercom, Hubspot
- **Chat Platforms** - Google Chat, OpenCX
- **Analytics** - DBT Cloud workflows

---

## 🛠️ Technology Stack

- **Language:** Python 3.11+
- **Data Processing:** pandas, numpy
- **APIs:** Google Cloud, ServiceM8, Intercom, Hubspot
- **Testing:** pytest
- **Secrets Management:** GitHub Secrets, Docker Secrets
- **Orchestration:** GitHub Actions
- **Data Warehouse:** Google BigQuery
- **BI Platform:** DBT Cloud

---

## 🔐 Security & Credentials

This repository uses a multi-layer security approach:

1. **Environment-Based Secrets**
   - `STAGING` - Development/testing environment
   - `PRODUCTION` - Live production environment

2. **Secret Management**
   - GitHub Secrets for CI/CD workflows
   - Docker Swarm Secrets for containerized deployments
   - Service account authentication for Google Cloud APIs

3. **Access Control**
   - Repository access restricted to authorized personnel only
   - Secrets never committed to version control
   - Environment variable injection at runtime

---

## 📦 Installation & Setup

### Prerequisites
```bash
# Python 3.11 or higher
python --version

# Install dependencies
pip install -r services/requirements.txt
```

### Configuration
```bash
# Set deployment environment
export DEPLOY_ENV=STAGING  # or PRODUCTION

# Secrets are managed via:
# - GitHub Secrets (for GitHub Actions)
# - Docker Secrets (for local development)
# - Environment variables (for manual runs)
```

### Running Modules
```bash
# Navigate to scripts directory
cd scripts

# Set Python path
export PYTHONPATH=/path/to/scripts

# Run a module
python -m src.stock_manager.main
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific module tests
PYTHONPATH=/home/Umusa/scripts pytest src/stock_manager/tests/

# Run with verbose output
pytest -v -s
```

---

## 📖 Documentation

Each module contains its own comprehensive README with:
- Module overview and purpose
- Setup and installation instructions
- Configuration details
- Usage examples
- Troubleshooting guides
- API documentation

See individual module READMEs for detailed information:
- [Stock Manager](src/stock_manager/README.md)
- [Services Documentation](services/README.md)

---

## 🤝 Development Guidelines

### Code Structure
- **Modular Design:** Follow the `script_template/` pattern
- **Configuration-Driven:** All settings in `config.py`
- **Separation of Concerns:** API handlers, data handlers, processors
- **Comprehensive Testing:** pytest with real reads, mocked writes
- **Documentation:** Clear README and inline docstrings

### Adding New Modules
1. Copy `src/script_template/` as starting point
2. Customize configuration in `config.py`
3. Implement business logic in processors
4. Add comprehensive tests
5. Document in README.md
6. Create Pull Request for review

---

## 📄 License & Legal

### Copyright Notice

```
Copyright © 2024-2025 Umusa Plumbing (Pty) Ltd. All Rights Reserved.

PROPRIETARY AND CONFIDENTIAL

This software and associated documentation files (the "Software") are 
proprietary to Umusa Plumbing (Pty) Ltd and are protected by copyright 
law and international treaties.

UNAUTHORIZED USE, REPRODUCTION, OR DISTRIBUTION IS STRICTLY PROHIBITED.
```

### Restrictions

❌ **The following are explicitly PROHIBITED without prior written authorization:**

- **Use** - Running, executing, or deploying this software
- **Reproduction** - Copying, duplicating, or replicating any portion
- **Distribution** - Sharing, publishing, or transmitting the code
- **Modification** - Altering, adapting, or creating derivative works
- **Reverse Engineering** - Decompiling, disassembling, or analyzing
- **Commercial Use** - Using for any commercial purpose outside Umusa Plumbing
- **Open Source Distribution** - Publishing under any open source license

### Authorized Use

✅ **Use of this software is ONLY authorized for:**

- Employees of Umusa Plumbing (Pty) Ltd during active employment
- Contractors engaged under written agreement with Umusa Plumbing
- Systems and infrastructure owned or controlled by Umusa Plumbing
- Business operations directly related to Umusa Plumbing services

### Termination of Rights

All rights to use this software terminate immediately upon:
- End of employment or contract with Umusa Plumbing
- Violation of any terms outlined in this notice
- Request by Umusa Plumbing management

### Legal Action

Unauthorized use of this software may result in:
- Civil litigation for damages
- Criminal prosecution under applicable law
- Injunctive relief to prevent further unauthorized use

### Contact

For licensing inquiries or authorization requests:
- **Company:** Umusa Plumbing (Pty) Ltd
- **Email:** legal@umusa.co.za
- **Website:** https://umusa.co.za

---

## 🆘 Support & Maintenance

### Internal Support
For Umusa Plumbing employees and authorized personnel:
- **Technical Issues:** Contact Development Team
- **Access Requests:** Contact IT Administration
- **Bug Reports:** Create GitHub Issue (internal use only)

### Emergency Contact
- **Critical System Failures:** Escalate to Platform Owner
- **Security Incidents:** Contact Security Team immediately
- **Data Issues:** Contact Data Engineering Team

---

## 📊 Monitoring & Operations

### Automated Workflows
- **Daily:** Stock inventory collection and aggregation
- **Weekly:** Consolidated reports and dashboards
- **On-Demand:** Manual script execution for ad-hoc analysis

### Logging & Alerts
- Application logs via Python logging module
- GitHub Actions workflow logs
- Error notifications via configured channels

### Performance
- Average execution time: 30-60 seconds per workflow
- API rate limits: Managed per service provider
- Data volume: Optimized for daily operational scale

---

## 📝 Changelog & Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and updates.

**Current Version:** 2.0.0 (Modular Architecture)
**Last Updated:** October 24, 2025

---

## ⚖️ Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL UMUSA
PLUMBING (PTY) LTD BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE.

---

**Maintained by:** Umusa Plumbing Development Team  
**Repository:** Private - Authorized Access Only  
**Last Review:** October 2025
