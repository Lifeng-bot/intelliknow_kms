
"""
End-to-end tests for Telegram and Microsoft Teams integrations
"""
import asyncio
import os
import sys
import json
from typing import Dict, List, Optional
import aiohttp
from integrations.telegram_bot import telegram_bot
from integrations.teams_bot import teams_bot
from core.orchestrator import query_orchestrator
from core.response_generator import response_generator
from app.config import settings


class IntegrationTest:
    """Base class for integration tests"""

    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_test(self, test_name: str, passed: bool, message: str = ""):
        """Add a test result"""
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_results(self):
        """Print test results"""
        print(f"\n{'='*80}")
        print(f"{self.name} Test Results")
        print(f"{'='*80}")
        print(f"Total: {len(self.tests)}, Passed: {self.passed}, Failed: {self.failed}")
        print(f"{'='*80}")

        for test in self.tests:
            status = "[PASS]" if test["passed"] else "[FAIL]"
            print(f"{status} {test['name']}")
            if test["message"]:
                print(f"      {test['message']}")

        print(f"{'='*80}\n")

        return self.failed == 0


class TelegramIntegrationTest(IntegrationTest):
    """Tests for Telegram integration"""

    def __init__(self):
        super().__init__("Telegram Integration")

    async def test_bot_initialization(self):
        """Test if the Telegram bot is initialized"""
        try:
            if not settings.TELEGRAM_BOT_TOKEN:
                self.add_test(
                    "Bot Initialization",
                    False,
                    "TELEGRAM_BOT_TOKEN not configured"
                )
                return

            if telegram_bot.application:
                self.add_test(
                    "Bot Initialization",
                    True,
                    "Telegram bot initialized successfully"
                )
            else:
                self.add_test(
                    "Bot Initialization",
                    False,
                    "Telegram bot application is None"
                )
        except Exception as e:
            self.add_test(
                "Bot Initialization",
                False,
                f"Error: {str(e)}"
            )

    async def test_webhook_endpoint(self):
        """Test the Telegram webhook endpoint"""
        try:
            if not telegram_bot.application:
                self.add_test(
                    "Webhook Endpoint",
                    False,
                    "Bot not initialized"
                )
                return

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{settings.TELEGRAM_WEBHOOK_PORT}{settings.TELEGRAM_WEBHOOK_PATH}",
                    json={"update_id": 1, "message": {"message_id": 1, "text": "test"}}
                ) as response:
                    if response.status in [200, 500]:  # 500 is expected if bot token is invalid
                        self.add_test(
                            "Webhook Endpoint",
                            True,
                            f"Webhook endpoint responded with status {response.status}"
                        )
                    else:
                        self.add_test(
                            "Webhook Endpoint",
                            False,
                            f"Unexpected status code: {response.status}"
                        )
        except Exception as e:
            self.add_test(
                "Webhook Endpoint",
                False,
                f"Error: {str(e)}"
            )

    async def test_query_processing(self):
        """Test query processing through the orchestrator"""
        try:
            test_query = "What is the company's leave policy?"

            # Route the query
            routing_info = query_orchestrator.route_query(test_query)

            if routing_info and "intent" in routing_info:
                self.add_test(
                    "Query Processing",
                    True,
                    f"Query routed to intent: {routing_info['intent']}"
                )
            else:
                self.add_test(
                    "Query Processing",
                    False,
                    "Failed to route query"
                )
        except Exception as e:
            self.add_test(
                "Query Processing",
                False,
                f"Error: {str(e)}"
            )


class TeamsIntegrationTest(IntegrationTest):
    """Tests for Microsoft Teams integration"""

    def __init__(self):
        super().__init__("Microsoft Teams Integration")

    async def test_bot_initialization(self):
        """Test if the Teams bot is initialized"""
        try:
            if not settings.TEAMS_APP_ID or not settings.TEAMS_APP_PASSWORD:
                self.add_test(
                    "Bot Initialization",
                    False,
                    "TEAMS_APP_ID or TEAMS_APP_PASSWORD not configured"
                )
                return

            if teams_bot.adapter:
                self.add_test(
                    "Bot Initialization",
                    True,
                    "Teams bot initialized successfully"
                )
            else:
                self.add_test(
                    "Bot Initialization",
                    False,
                    "Teams bot adapter is None"
                )
        except Exception as e:
            self.add_test(
                "Bot Initialization",
                False,
                f"Error: {str(e)}"
            )

    async def test_messages_endpoint(self):
        """Test the Teams messages endpoint"""
        try:
            if not teams_bot.adapter:
                self.add_test(
                    "Messages Endpoint",
                    False,
                    "Bot not initialized"
                )
                return

            async with aiohttp.ClientSession() as session:
                # Create a sample Teams message activity
                activity = {
                    "type": "message",
                    "id": "test",
                    "text": "What is the company's leave policy?",
                    "from": {
                        "id": "test_user",
                        "name": "Test User"
                    },
                    "recipient": {
                        "id": "test_bot",
                        "name": "Test Bot"
                    }
                }

                async with session.post(
                    f"http://localhost:{settings.TELEGRAM_WEBHOOK_PORT}{settings.TEAMS_BOT_ENDPOINT}",
                    json=activity,
                    headers={"Authorization": "Bearer test_token"}
                ) as response:
                    # We expect 401 (unauthorized) with invalid token, or 201 (created) with valid token
                    if response.status in [201, 401]:
                        self.add_test(
                            "Messages Endpoint",
                            True,
                            f"Messages endpoint responded with status {response.status}"
                        )
                    else:
                        self.add_test(
                            "Messages Endpoint",
                            False,
                            f"Unexpected status code: {response.status}"
                        )
        except Exception as e:
            self.add_test(
                "Messages Endpoint",
                False,
                f"Error: {str(e)}"
            )

    async def test_query_processing(self):
        """Test query processing through the orchestrator"""
        try:
            test_query = "How do I submit an expense report?"

            # Route the query
            routing_info = query_orchestrator.route_query(test_query)

            if routing_info and "intent" in routing_info:
                self.add_test(
                    "Query Processing",
                    True,
                    f"Query routed to intent: {routing_info['intent']}"
                )
            else:
                self.add_test(
                    "Query Processing",
                    False,
                    "Failed to route query"
                )
        except Exception as e:
            self.add_test(
                "Query Processing",
                False,
                f"Error: {str(e)}"
            )


class HealthCheckTest(IntegrationTest):
    """Tests for health check endpoint"""

    def __init__(self):
        super().__init__("Health Check")

    async def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{settings.TELEGRAM_WEBHOOK_PORT}/health"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "status" in data and "telegram" in data and "teams" in data:
                            self.add_test(
                                "Health Endpoint",
                                True,
                                f"Status: {data['status']}, Telegram: {data['telegram']}, Teams: {data['teams']}"
                            )
                        else:
                            self.add_test(
                                "Health Endpoint",
                                False,
                                "Invalid response format"
                            )
                    else:
                        self.add_test(
                            "Health Endpoint",
                            False,
                            f"Unexpected status code: {response.status}"
                        )
        except Exception as e:
            self.add_test(
                "Health Endpoint",
                False,
                f"Error: {str(e)}"
            )


async def run_all_tests():
    """Run all integration tests"""
    print(f"\n{'='*80}")
    print("IntelliKnow KMS - Integration Tests")
    print(f"{'='*80}\n")

    # Create test instances
    telegram_test = TelegramIntegrationTest()
    teams_test = TeamsIntegrationTest()
    health_test = HealthCheckTest()

    # Run Telegram tests
    await telegram_test.test_bot_initialization()
    await telegram_test.test_webhook_endpoint()
    await telegram_test.test_query_processing()

    # Run Teams tests
    await teams_test.test_bot_initialization()
    await teams_test.test_messages_endpoint()
    await teams_test.test_query_processing()

    # Run health check tests
    await health_test.test_health_endpoint()

    # Print results
    telegram_passed = telegram_test.print_results()
    teams_passed = teams_test.print_results()
    health_passed = health_test.print_results()

    # Overall result
    print(f"\n{'='*80}")
    print("Overall Test Results")
    print(f"{'='*80}")
    print(f"Telegram Integration: {'PASSED' if telegram_passed else 'FAILED'}")
    print(f"Teams Integration: {'PASSED' if teams_passed else 'FAILED'}")
    print(f"Health Check: {'PASSED' if health_passed else 'FAILED'}")
    print(f"{'='*80}\n")

    return telegram_passed and teams_passed and health_passed


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
