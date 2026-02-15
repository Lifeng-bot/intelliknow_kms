
# Integration Tests for Telegram and Microsoft Teams

This document provides instructions for running the integration tests for the Telegram and Microsoft Teams integrations.

## Prerequisites

Before running the integration tests, ensure you have:

1. Installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configured the environment variables in `.env` file:
   - For Telegram tests: `TELEGRAM_BOT_TOKEN`
   - For Teams tests: `TEAMS_APP_ID`, `TEAMS_APP_PASSWORD`, `TEAMS_APP_TENANT_ID`

3. Started the bot server:
   ```bash
   python start_bots.py
   ```

## Running the Tests

To run all integration tests:

```bash
python scripts/test_integrations.py
```

## Test Coverage

The integration tests cover the following areas:

### Telegram Integration Tests

1. **Bot Initialization**
   - Verifies that the Telegram bot is properly initialized
   - Checks if the bot token is configured

2. **Webhook Endpoint**
   - Tests the Telegram webhook endpoint
   - Verifies that the endpoint responds correctly to requests

3. **Query Processing**
   - Tests query processing through the orchestrator
   - Verifies that queries are routed to the correct intent

### Microsoft Teams Integration Tests

1. **Bot Initialization**
   - Verifies that the Teams bot is properly initialized
   - Checks if the bot credentials are configured

2. **Messages Endpoint**
   - Tests the Teams messages endpoint
   - Verifies that the endpoint responds correctly to requests

3. **Query Processing**
   - Tests query processing through the orchestrator
   - Verifies that queries are routed to the correct intent

### Health Check Tests

1. **Health Endpoint**
   - Tests the health check endpoint
   - Verifies that the endpoint returns the correct status

## Test Results

After running the tests, you will see a summary of the results:

```
================================================================================
IntelliKnow KMS - Integration Tests
================================================================================

================================================================================
Telegram Integration Test Results
================================================================================
Total: 3, Passed: 3, Failed: 0
================================================================================
[PASS] Bot Initialization
      Telegram bot initialized successfully
[PASS] Webhook Endpoint
      Webhook endpoint responded with status 200
[PASS] Query Processing
      Query routed to intent: HR
================================================================================

================================================================================
Microsoft Teams Integration Test Results
================================================================================
Total: 3, Passed: 3, Failed: 0
================================================================================
[PASS] Bot Initialization
      Teams bot initialized successfully
[PASS] Messages Endpoint
      Messages endpoint responded with status 201
[PASS] Query Processing
      Query routed to intent: Finance
================================================================================

================================================================================
Health Check Test Results
================================================================================
Total: 1, Passed: 1, Failed: 0
================================================================================
[PASS] Health Endpoint
      Status: healthy, Telegram: enabled, Teams: enabled
================================================================================

================================================================================
Overall Test Results
================================================================================
Telegram Integration: PASSED
Teams Integration: PASSED
Health Check: PASSED
================================================================================
```

## Troubleshooting

### Tests Fail with "Bot not initialized"

**Cause:** The bot token or credentials are not configured in the `.env` file.

**Solution:** Add the required environment variables to your `.env` file:
- For Telegram: `TELEGRAM_BOT_TOKEN`
- For Teams: `TEAMS_APP_ID`, `TEAMS_APP_PASSWORD`, `TEAMS_APP_TENANT_ID`

### Tests Fail with "Connection refused"

**Cause:** The bot server is not running.

**Solution:** Start the bot server:
```bash
python start_bots.py
```

### Tests Fail with "Unexpected status code"

**Cause:** The bot server is not responding correctly.

**Solution:** Check the bot server logs for errors and ensure it's running correctly.

## Continuous Integration

These tests can be integrated into a CI/CD pipeline to ensure that the integrations work correctly after each deployment.

Example GitHub Actions workflow:

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Start bot server
        run: |
          python start_bots.py &
          sleep 10
      - name: Run integration tests
        run: |
          python scripts/test_integrations.py
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TEAMS_APP_ID: ${{ secrets.TEAMS_APP_ID }}
          TEAMS_APP_PASSWORD: ${{ secrets.TEAMS_APP_PASSWORD }}
          TEAMS_APP_TENANT_ID: ${{ secrets.TEAMS_APP_TENANT_ID }}
```

## Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Microsoft Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Azure Bot Service Documentation](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-overview)
