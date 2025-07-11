# GraphMCP Refactoring Quick Reference

## 🎯 Goals
- Clean architecture (UI/Workflow separation)
- Mock/Real mode switching
- Enhanced workflow control (pause/resume)
- Better progress tracking
- Maintainable, testable code

## 📁 New Structure
```
concrete/
├── ui/           # Streamlit UI components
│   ├── app.py
│   ├── components/
│   ├── state/
│   └── layouts/
└── workflow/     # Workflow logic
    ├── manager.py
    ├── progress.py
    ├── steps/
    └── mock/
```

## 🔧 Key Components

### UI Components
- **WorkflowControls**: Start/Stop/Pause buttons
- **LogStream**: Live-updating logs
- **ProgressTables**: File processing status

### Workflow Components
- **WorkflowManager**: Orchestrates execution
- **ProgressTracker**: Tracks batch progress
- **BaseWorkflowStep**: Common step interface

## 🧪 Mock Flags
```python
USE_MOCK_PACK = True       # Local XML file
USE_MOCK_DISCOVERY = True  # Local JSON file
USE_MOCK_PROCESSING = True # Simulate processing
```

## 📊 Test Data
- **Repo**: `tests/data/postgres_sample_dbs_packed.xml`
- **Discovery**: `tests/data/discovery_outcome_context.json`
- **Database**: postgres_air

## 🚀 Quick Start
```bash
# Run tests
make graphmcp-test-unit
make graphmcp-test-integration

# Run UI (after refactoring)
streamlit run concrete/ui/app.py

# Run with mocks
USE_MOCK_PACK=true streamlit run concrete/ui/app.py
```

## ⚠️ Important Notes
1. **Preserve working code** - Copy from legacy/
2. **Mock first** - Real implementation later
3. **Test everything** - Unit → Integration → E2E
4. **Document changes** - Update memories/rules
5. **Performance matters** - <2s load, <100ms response

## 📝 Checklist
- [ ] Phase 0: Cleanup & Legacy
- [ ] Phase 1: UI Implementation
- [ ] Phase 2: Workflow Implementation
- [ ] Phase 3: Testing
- [ ] Phase 4: Migration
- [ ] Phase 5: Documentation

## 🔗 Resources
- Main Plan: `plan/grand-refac-plan.md`
- Implementation Guide: `plan/implementation-guide.md`
- Pitfalls: `plan/pitfalls-and-considerations.md`
- Summary: `plan/refactoring-summary.md` 