# Configuration Directory

This directory contains configuration files and templates for the AI Companion project.

## Files

### `config.yaml`
Main configuration file containing:
- Model paths and settings
- API configurations
- Audio processing parameters
- Live2D model settings
- Application runtime parameters

### `config_template.yaml`
Template configuration file for new installations:
- Contains default values and structure
- Used by setup system to create functional defaults
- Documents all available configuration options

### `.secrets.template`
Template for secrets and API keys:
- Contains placeholder values for sensitive information
- Used to generate `.secrets` file during setup
- Never contains actual secret values

## Usage

1. **New Installation**: The setup system uses these templates to create working configurations
2. **Configuration Updates**: Modify `config.yaml` for runtime settings
3. **Secrets Management**: Create `.secrets` file based on `.secrets.template`

## Security Notes

- The `.secrets` file (when created) should never be committed to version control
- The templates contain no sensitive information
- All actual secrets are generated or provided during setup
