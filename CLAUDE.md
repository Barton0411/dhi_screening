# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DHI筛查助手 (DHI Screening Assistant) is a PyQt6 desktop application for dairy herd health management. It analyzes DHI (Dairy Herd Improvement) test data to help farms monitor cattle health across three main modules:
- **DHI基础筛选**: Multi-dimensional filtering on 23 indicators with weighted average calculations
- **隐性乳房炎监测**: Mastitis monitoring with 6 key performance indicators
- **尿素氮追踪分析**: Urea nitrogen tracking across 12 lactation stages

## Development Commands

```bash
# Run the application
python fast_start.py          # Preferred - includes splash screen
python desktop_app.py         # Direct launch

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Build for macOS
./build_macos.sh              # Uses DHI_Screening_System_macOS.spec

# Build for Windows
pyinstaller DHI_Screening_System_Windows.spec
```

## Architecture

**Entry Points**:
- `fast_start.py` - Launcher with splash screen (preferred)
- `desktop_app.py` - Main PyQt6 GUI application (~452KB, core logic)

**Core Modules**:
- `data_processor.py` - Data loading, validation, filtering engine
- `mastitis_monitoring.py` - Mastitis metrics calculation
- `urea_tracker.py` - Urea nitrogen analysis with pyqtgraph visualization
- `auth_module/` - Aliyun MySQL authentication (login, registration, password management)

**Configuration**:
- `config.yaml` - App settings (version, upload limits, logging)
- `rules.yaml` - Business rules, field mappings (23 DHI indicators), old/new format compatibility

**Data Flow**: ZIP/Excel input → format detection → field mapping → validation → analysis → Excel export

## Key Technical Details

- **Authentication**: Aliyun Polardb MySQL with Fernet-encrypted local credentials and single-device login
- **Async Processing**: QThread workers for file processing (`FileUploadWorker`, `FilteringWorker`)
- **DPI Awareness**: Responsive scaling for different screen resolutions
- **Localization**: Complete Chinese UI including pyqtgraph chart menus (`chart_localization.py`)

## Git Commit Conventions

Use type prefixes: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`

Maintain `CHANGELOG.md` with version history following the existing format.
