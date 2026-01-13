"""
Example: How to setup and run Monitor with Wallet.

This demonstrates how to:
1. Initialize Services and Storage.
2. Configure and create Monitor.
3. Add default tasks.
4. Create MonitorDaemon and start it in background.
5. Initialize Wallet with Monitor.
"""

import logging
import os
import sys
import time

# Add src to path for execution without installation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from bsv_wallet_toolbox.monitor.monitor import Monitor, MonitorOptions
from bsv_wallet_toolbox.monitor.monitor_daemon import MonitorDaemon
from bsv_wallet_toolbox.services.services import Services
from bsv_wallet_toolbox.storage.provider import StorageProvider
from bsv_wallet_toolbox.wallet import Wallet


def main() -> None:
    """Run monitor demo."""
    chain = "test"

    print("--- Monitor Integration Demo ---")

    # 1. Initialize Dependencies
    print("Initializing Services and Storage...")
    services = Services(chain)
    # Note: In real app, use persistent DB file (e.g., "sqlite:///wallet.db")
    storage = StorageProvider("sqlite:///:memory:")

    # 2. Setup Monitor
    print("Configuring Monitor...")
    monopts = MonitorOptions(chain=chain, storage=storage, services=services)
    monitor = Monitor(monopts)
    monitor.add_default_tasks()
    print(f"Monitor configured with {len(monitor._tasks)} tasks.")

    # 3. Start Monitor Daemon (Background Thread)
    print("Starting Monitor Daemon...")
    daemon = MonitorDaemon(monitor)
    daemon.start()
    print("Monitor daemon started in background.")

    # 4. Initialize Wallet
    print("Initializing Wallet with Monitor...")
    # (Assuming minimal wallet setup for demo)
    wallet = Wallet(
        chain=chain,
        services=services,
        storage_provider=storage,
        monitor=monitor,
    )

    print(f"Wallet {wallet.VERSION} ready.")
    print("Monitor is now running in the background, checking for transactions and proofs.")

    try:
        # Keep main thread alive to let daemon run
        # In a real app (e.g. Flask), the web server keeps the process alive
        for i in range(5):
            print(f"Main application running... {i}/5")
            # Simulate app activity
            # wallet.get_version({})
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Stopping Monitor Daemon...")
        daemon.stop()
        print("Monitor daemon stopped.")


if __name__ == "__main__":
    main()
