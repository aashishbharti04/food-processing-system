"""Enable ``python -m food_processing_system``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
