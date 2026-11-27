
import logging
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

# Configuration
HEALTH_URL = "http://localhost:8000/health"
CONTAINER_NAME = "support-app"

CHECK_INTERVAL = 10
FAILURE_THRESHOLD = 3
RESTART_COOLDOWN = 60

failure_count = 0
last_restart_time = 0

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
    Path(__file__).resolve().parent / "recovery_agent.log"
),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("self-healing-agent")


def check_application_health():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as response:
            return response.status == 200

    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def restart_application():
    global last_restart_time

    logger.warning("Application failure detected. Initiating recovery.")

    try:
        result = subprocess.run(
            ["docker", "restart", CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        logger.info("Docker restart completed: %s", result.stdout.strip())
        last_restart_time = time.time()

        for attempt in range(12):
            if check_application_health():
                logger.info("SELF-HEALING SUCCESS: Application recovered.")
                return True

            logger.info("Waiting for application recovery...")
            time.sleep(5)

        logger.error("SELF-HEALING FAILED: Application did not recover.")
        return False

    except Exception:
        logger.exception("Application restart failed.")
        last_restart_time = time.time()
        return False


def monitor_application():
    global failure_count

    logger.info("Self-healing agent started.")
    logger.info("Monitoring %s", HEALTH_URL)

    while True:
        if check_application_health():
            if failure_count > 0:
                logger.info("Application health restored.")

            failure_count = 0
            logger.info("Application status: UP")

        else:
            failure_count += 1
            logger.warning(
                "Application health check failed (%s/%s)",
                failure_count,
                FAILURE_THRESHOLD
            )

            if failure_count >= FAILURE_THRESHOLD:
                if time.time() - last_restart_time >= RESTART_COOLDOWN:
                    restart_application()
                else:
                    logger.warning("Restart skipped: cooldown active")

                failure_count = 0

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        monitor_application()
    except KeyboardInterrupt:
        logger.info("Self-healing agent stopped by user.")
