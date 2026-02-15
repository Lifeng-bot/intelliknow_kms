
"""
Start script for running Telegram and Microsoft Teams bots
"""
import asyncio
import sys
import logging
from integrations.telegram_bot import telegram_bot
from integrations.teams_bot import teams_bot
from aiohttp import web
from botbuilder.schema import Activity
from botbuilder.core import BotFrameworkAdapter, TurnContext
from app.config import settings

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def telegram_webhook_handler(request):
    """Handle Telegram webhook requests."""
    if not telegram_bot.application:
        logger.error("Telegram bot not initialized")
        return web.Response(status=500)

    try:
        # Process the update
        await telegram_bot.application.update_queue.put(
            await request.json()
        )
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        return web.Response(status=500)


async def teams_messages_handler(request):
    """Handle Microsoft Teams messages."""
    if not teams_bot.adapter:
        logger.error("Teams bot not initialized")
        return web.Response(status=500)

    try:
        # Get the activity from the request
        body = await request.json()
        activity = Activity().deserialize(body)

        # Authenticate the request
        auth_header = request.headers.get("Authorization", "")

        # Process the activity
        response = await teams_bot.adapter.process_activity(
            activity,
            auth_header,
            teams_bot.on_turn
        )

        if response:
            return web.Response(
                status=response.status,
                text=response.body
            )

        return web.Response(status=201)
    except Exception as e:
        logger.error(f"Error processing Teams message: {e}")
        return web.Response(status=500)


async def health_check(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "telegram": "enabled" if telegram_bot.application else "disabled",
        "teams": "enabled" if teams_bot.adapter else "disabled"
    })


async def start_server():
    """Start the web server for both bots."""
    app = web.Application()

    # Add routes for Telegram
    if telegram_bot.application:
        app.router.add_post(
            settings.TELEGRAM_WEBHOOK_PATH,
            telegram_webhook_handler
        )
        logger.info(f"Telegram webhook endpoint registered: {settings.TELEGRAM_WEBHOOK_PATH}")

    # Add routes for Teams
    if teams_bot.adapter:
        app.router.add_post(
            settings.TEAMS_BOT_ENDPOINT,
            teams_messages_handler
        )
        logger.info(f"Teams messages endpoint registered: {settings.TEAMS_BOT_ENDPOINT}")

    # Add health check endpoint
    app.router.add_get("/health", health_check)
    logger.info("Health check endpoint registered: /health")

    # Start the server
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        settings.TELEGRAM_WEBHOOK_PORT
    )

    logger.info(f"Starting web server on port {settings.TELEGRAM_WEBHOOK_PORT}")
    await site.start()

    return runner


async def main():
    """Main function to run both bots."""
    logger.info("Starting IntelliKnow KMS Bots...")

    # Check if any bot is configured
    if not telegram_bot.application and not teams_bot.adapter:
        logger.error("No bots configured. Please set TELEGRAM_BOT_TOKEN or TEAMS_APP_ID/TEAMS_APP_PASSWORD.")
        sys.exit(1)

    # Start the web server
    runner = await start_server()

    # Keep the server running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
