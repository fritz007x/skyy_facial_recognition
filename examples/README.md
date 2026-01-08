# Examples

This directory contains example code demonstrating how to use the Skyy Facial Recognition system.

## Available Examples

### basic_recognition.py
Simple example showing how to connect to the MCP server and perform basic operations:
- List available tools
- Check system health
- List registered users

```bash
python examples/basic_recognition.py
```

## Prerequisites

1. **Start the MCP server:**
   ```bash
   python src/skyy_facial_recognition_mcp.py
   ```

2. **Configure OAuth (if required):**
   See `docs/developer/oauth-implementation.md` for setup instructions.

## More Information

- [User Guides](../docs/user-guides/) - Installation and usage
- [API Reference](../docs/api/) - MCP tool documentation
- [Developer Guide](../docs/developer/) - Architecture and integration
