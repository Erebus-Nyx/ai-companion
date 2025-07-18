# Scripts Directory Organization

This directory contains all standalone scripts for the AI Companion project, organized by functionality.

## Directory Structure

### `/migration/`
Scripts for database management, migration, and cleanup:
- `check_and_clean_db.py` - Database integrity checks and cleanup
- `check_motions.py` - Motion data validation
- `clean_ai_companion_db.py` - Clean AI companion database
- `clear_database.py` - Clear database contents
- `migrate_config.py` - Configuration migration
- `migrate_preview_column.py` - Preview column migration
- `migrate_pyannote_models.py` - Pyannote model migration
- `migrate_to_separated_dbs.py` - Migrate to separated databases
- `migration_report.py` - Generate migration reports

### `/setup/`
Scripts for initial setup, installation, and data population:
- `build_pipx.sh` - Build package with pipx
- `download_live2d_dependencies.sh` - Download Live2D dependencies
- `install_live2d_models.py` - Install Live2D models
- `populate_all_motions.py` - Populate motion data
- `populate_correct_paths.py` - Fix and populate correct paths
- `populate_live2d_separated.py` - Populate Live2D separated database
- `populate_model_personalities.py` - Populate model personality data
- `setup.py` - Legacy setup script

### `/testing/`
Test scripts and validation utilities:
- `test_avatar_emotions.py` - Test avatar emotion system
- `test_caching_fix.py` - Test caching functionality
- `test_chat.py` - Test chat functionality
- `test_config_only.py` - Test configuration only
- `test_direct_enhanced_vad.py` - Test enhanced VAD directly
- `test_embedded_llm_memory.py` - Test embedded LLM memory
- `test_enhanced_pipeline.py` - Test enhanced pipeline
- `test_enhanced_vad.py` - Test enhanced VAD
- `test_enhanced_vad_minimal.py` - Test minimal enhanced VAD
- `test_fallback_system.py` - Test fallback system
- `test_full_download.py` - Test full download functionality
- `test_full_local_git_download.py` - Test local git downloads
- `test_llm_simple.py` - Test simple LLM functionality
- `test_local_git_models.py` - Test local git model handling
- `test_model_downloads.py` - Test model download functionality
- `test_production_service.py` - Test production service
- `test_quick_cache.py` - Test quick cache functionality
- `test_silero.py` - Test Silero VAD
- `test_var_and_diarization.py` - Test VAR and diarization
- `test_webapp.py` - Test web application
- `tests_README.md` - Original tests documentation

### `/deployment/`
Scripts for running the application and deployment:
- `ai_companion_main.py` - Main application entry point
- `cloudflare-setup.sh` - Cloudflare setup script
- `complete_live2d_fix.py` - Complete Live2D fixes
- `deploy.sh` - Main deployment script
- `deploy_live2d_integration.sh` - Deploy Live2D integration
- `enhanced_vad_example.py` - Enhanced VAD example
- `install-systemd-service.sh` - Install systemd service
- `run_app.py` - Application runner
- `service-manager.sh` - Service management utilities

### `/debug/`
Debug utilities and diagnostic tools:
- `debug_api_issue.py` - Debug API issues
- `debug_motion_test.py` - Debug motion functionality
- `emergency_borders.js` - Emergency UI borders debug
- `verify_build.py` - Build verification
- `verify_port_change.sh` - Verify port configuration changes

## Usage Guidelines

1. **Migration Scripts**: Run these when updating database schemas or migrating data
2. **Setup Scripts**: Use during initial installation or when adding new components
3. **Testing Scripts**: Run these to validate functionality and test components
4. **Deployment Scripts**: Use these to start and deploy the application
5. **Debug Scripts**: Use when troubleshooting issues or diagnosing problems

## File Organization Principles

- **Single Responsibility**: Each script has a clear, focused purpose
- **Categorization**: Scripts are grouped by their primary function
- **Documentation**: Each category includes scripts that are self-documenting
- **Maintenance**: Regular cleanup ensures only current, working scripts remain
