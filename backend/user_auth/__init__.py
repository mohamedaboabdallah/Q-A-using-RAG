"""
Core Utilities Module

This module aggregates and exposes functionalities from the
`files_handling` and `tokens_handling` modules.

- `files_handling`: Provides utilities for managing user and file data persistence,
  including JSON loading/saving and file metadata management.

- `tokens_handling`: Implements JWT token generation and validation utilities
  for securing Flask API endpoints.

By importing these modules here, this module serves as a centralized
access point for core backend services related to file management
and user authentication.
"""
from . import files_handling
from . import tokens_handling
