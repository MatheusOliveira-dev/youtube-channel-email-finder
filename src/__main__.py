"""Package entry point, so both `python -m src` (Apify CLI) and the Dockerfile
start the actor the same way."""
import asyncio

from .main import main

asyncio.run(main())
