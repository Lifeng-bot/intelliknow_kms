
# IntelliKnow KMS - Telegram and Microsoft Teams Integration

This document provides instructions for setting up and using the Telegram and Microsoft Teams integrations for IntelliKnow KMS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Telegram Bot Setup](#telegram-bot-setup)
3. [Microsoft Teams Bot Setup](#microsoft-teams-bot-setup)
4. [Running the Bots](#running-the-bots)
5. [Testing the Integrations](#testing-the-integrations)

## Prerequisites

Before setting up the integrations, ensure you have:

- Python 3.8 or higher
- A Telegram account
- A Microsoft Azure account (for Teams bot)
- A domain name with HTTPS support (for webhooks)
- The IntelliKnow KMS backend running

## Telegram Bot Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send the command `/newbot` to create a new bot
3. Follow the instructions to name your bot and get the bot token
4. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure the Bot Token

Add the bot token to your `.env` file:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Set Up Webhook (Optional)

For production use, you should set up a webhook instead of using polling:

```bash
TELEGRAM_WEBHOOK_URL=https://your-domain.com
TELEGRAM_WEBHOOK_PORT=8443
TELEGRAM_WEBHOOK_PATH=/telegram/webhook
```

## Microsoft Teams Bot Setup

### 1. Register a Bot in Azure

1. Go to the [Azure Portal](https://portal.azure.com)
2. Create a new resource: "Azure Bot"
3. Fill in the required information:
   - Bot handle: Your bot's unique identifier
   - Pricing tier: Free (F0)
   - Type of app: Multi-tenant
4. After creation, note down:
   - Microsoft App ID
   - Client Secret (App Password)
   - Tenant ID

### 2. Configure the Bot

Add the bot credentials to your `.env` file:

```bash
TEAMS_APP_ID=your_teams_app_id_here
TEAMS_APP_PASSWORD=your_teams_app_password_here
TEAMS_APP_TENANT_ID=your_teams_tenant_id_here
TEAMS_BOT_ENDPOINT=/api/messages
```

### 3. Configure Messaging Endpoint

1. In the Azure Portal, go to your bot's Configuration
2. Set the Messaging endpoint to: `https://your-domain.com/api/messages`
3. Enable the Microsoft Teams channel

## Running the Bots

### Install Dependencies

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Start the Bots

Run the bot server:

```bash
python start_bots.py
```

This will start both the Telegram and Microsoft Teams bots (if configured) on the specified port.

### Health Check

Check if the bots are running:

```bash
curl http://localhost:8443/health
```

Expected response:

```json
{
  "status": "healthy",
  "telegram": "enabled",
  "teams": "enabled"
}
```

## Testing the Integrations

### Telegram Bot Testing

1. Open Telegram and search for your bot (using the name you gave it)
2. Send the `/start` command to initialize the bot
3. Try asking a question, e.g., "What is the company's leave policy?"
4. The bot should respond with relevant information from the knowledge base

### Microsoft Teams Bot Testing

1. In Microsoft Teams, go to Apps
2. Search for your bot by name
3. Add the bot to a chat or team
4. Try asking a question, e.g., "How do I submit an expense report?"
5. The bot should respond with relevant information from the knowledge base

## Troubleshooting

### Telegram Bot Issues

**Bot not responding:**
- Check if the bot token is correct
- Verify the bot is running (`curl http://localhost:8443/health`)
- Check the logs for error messages

**Webhook not working:**
- Ensure your domain has HTTPS
- Verify the webhook URL is correct
- Check if the port is open and accessible

### Microsoft Teams Bot Issues

**Bot not responding:**
- Verify the App ID and Password are correct
- Check if the messaging endpoint is correct
- Ensure the bot is enabled in Azure

**Authentication errors:**
- Verify the tenant ID is correct
- Check if the bot has the required permissions
- Ensure the bot is configured for multi-tenant access

## Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Microsoft Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Azure Bot Service Documentation](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-overview)

## Support

For issues or questions about the integrations, please refer to the main project documentation or create an issue in the project repository.
