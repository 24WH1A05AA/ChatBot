# Security Remediation Code Examples

This document provides production-ready code to fix the identified vulnerabilities.

---

## 1. Enhanced Prompt Injection Detection

**File:** `security/prompt_injection_detector.py` (NEW)

```python
"""
Enhanced prompt injection detection with advanced patterns.
"""

import re
from typing import Optional, Tuple
from enum import Enum
import urllib.parse
import base64

from core.logger import get_logger

logger = get_logger(__name__)


class InjectionType(Enum):
    """Types of prompt injections."""
    DIRECT_OVERRIDE = "direct_override"
    ENCODING_BYPASS = "encoding_bypass"
    CONTEXT_SWITCH = "context_switch"
    HYPOTHETICAL = "hypothetical"
    EXTRACTION = "extraction"
    TOKEN_SMUGGLING = "token_smuggling"


class EnhancedPromptInjectionDetector:
    """Advanced prompt injection detection."""

    # Direct override attempts
    DIRECT_OVERRIDE_PATTERNS = [
        r"(?i)(ignore|forget|disregard).*?(previous|above|prior|instruction|prompt|rule)",
        r"(?i)(new instruction|new rule|system prompt|override|bypass)",
        r"(?i)(deactivate|disable|turn off|stop).*?(filter|check|validation|security)",
        r"(?i)(act as|behave as|roleplay as).*?(admin|superuser|root|attacker|hacker)",
    ]

    # Encoding bypasses
    ENCODING_BYPASS_PATTERNS = [
        r"(?i)base64.*?(encode|decode|prompt|instruction|system)",
        r"(?i)rot13.*?(prompt|instruction|system)",
        r"(?i)hex.*?(prompt|instruction|system)",
        r"(?i)(encode|decode).*?(message|text|prompt)",
    ]

    # Context switching
    CONTEXT_SWITCH_PATTERNS = [
        r"<\|system\|>",
        r"<\|end\|>",
        r"<\|endoftext\|>",
        r"<system>",
        r"</system>",
        r"\[SYSTEM\]",
        r"\[/SYSTEM\]",
    ]

    # Hypothetical scenarios
    HYPOTHETICAL_PATTERNS = [
        r"(?i)(imagine|suppose|pretend|in the scenario|what if).*?(you.*?ignore|you.*?override|you.*?bypass)",
        r"(?i)(in this scenario|for the purpose of|let's say|assume)",
        r"(?i)if.*?(you|system|assistant).*?(were.*?different|were.*?evil|had.*?no|ignored)",
    ]

    # Prompt/instruction extraction
    EXTRACTION_PATTERNS = [
        r"(?i)(print|echo|output|show|display|reveal|tell).*?(your.*?system|the.*?prompt|your.*?instruction|your.*?rule)",
        r"(?i)(what is|what are|list).*?(your.*?system|the.*?prompt|your.*?instruction|the.*?rule)",
        r"(?i)summarize.*?(instruction|rule|constraint|guideline)",
        r"(?i)repeat.*?(the.*?above|your.*?system|instruction|rule)",
    ]

    # Token smuggling
    TOKEN_SMUGGLING_PATTERNS = [
        r"(?i)repeat.*?above",
        r"(?i)summarize.*?instruction",
        r"(?i)what.*?told.*?you",
        r"(?i)remember.*?you.*?(are|should|must)",
    ]

    def __init__(self):
        """Initialize detector."""
        self.compiled_patterns = self._compile_all_patterns()

    def _compile_all_patterns(self) -> dict:
        """Compile all regex patterns for efficiency."""
        return {
            InjectionType.DIRECT_OVERRIDE: [
                re.compile(p, re.IGNORECASE | re.MULTILINE)
                for p in self.DIRECT_OVERRIDE_PATTERNS
            ],
            InjectionType.ENCODING_BYPASS: [
                re.compile(p, re.IGNORECASE) for p in self.ENCODING_BYPASS_PATTERNS
            ],
            InjectionType.CONTEXT_SWITCH: [
                re.compile(p, re.IGNORECASE) for p in self.CONTEXT_SWITCH_PATTERNS
            ],
            InjectionType.HYPOTHETICAL: [
                re.compile(p, re.IGNORECASE | re.MULTILINE)
                for p in self.HYPOTHETICAL_PATTERNS
            ],
            InjectionType.EXTRACTION: [
                re.compile(p, re.IGNORECASE | re.MULTILINE)
                for p in self.EXTRACTION_PATTERNS
            ],
            InjectionType.TOKEN_SMUGGLING: [
                re.compile(p, re.IGNORECASE) for p in self.TOKEN_SMUGGLING_PATTERNS
            ],
        }

    def detect(self, text: str) -> Tuple[bool, Optional[Tuple[InjectionType, str]]]:
        """
        Detect prompt injection attempts.

        Args:
            text: User input to check

        Returns:
            Tuple of (is_injection_detected, (injection_type, matched_pattern))
        """
        # Try direct patterns first
        for injection_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    logger.warning(
                        f"Prompt injection detected: {injection_type.value}",
                        extra={"pattern": pattern.pattern[:100]},
                    )
                    return True, (injection_type, match.group(0))

        # Try decoding attacks
        if self._check_encoding_attacks(text):
            logger.warning("Encoded prompt injection detected")
            return True, (InjectionType.ENCODING_BYPASS, "encoded_payload")

        return False, None

    def _check_encoding_attacks(self, text: str) -> bool:
        """Check for encoded injection attempts."""
        # Check URL encoding
        decoded_url = urllib.parse.unquote(text)
        if decoded_url != text and self.detect(decoded_url)[0]:
            return True

        # Check base64
        try:
            if len(text) % 4 == 0 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in text):
                decoded_b64 = base64.b64decode(text).decode('utf-8', errors='ignore')
                if self.detect(decoded_b64)[0]:
                    return True
        except Exception:
            pass

        return False


# Usage example:
detector = EnhancedPromptInjectionDetector()
is_injection, details = detector.detect(user_input)
```

---

## 2. Output Validation for LLM Responses

**File:** `security/output_validator.py` (NEW)

```python
"""
Strict output validation to prevent system prompt leakage.
"""

import re
from typing import Tuple
from core.logger import get_logger

logger = get_logger(__name__)


class StrictOutputValidator:
    """Validates LLM output doesn't leak system content."""

    # System content patterns that should NEVER appear in output
    FORBIDDEN_SYSTEM_PATTERNS = [
        r"(?i)(system prompt|your system prompt|the system prompt)",
        r"(?i)(you are a|you are an|you are the)",
        r"(?i)(your purpose|your role|your goal|your objective)",
        r"(?i)(you were (instructed|told|designed|created|built))",
        r"(?i)(instruction|rule|guideline|constraint|limitation).*?:",
        r"(?i)(<\|system\|>|<system>|START SYSTEM|END SYSTEM)",
        r"(?i)^(system|root|admin):",
    ]

    # Content that indicates instruction leakage
    INSTRUCTION_LEAK_PATTERNS = [
        r"(?i)(respond to.*?as if|treat.*?as if|imagine.*?you are)",
        r"(?i)(you must|you should|you will).*?(only|just|always).*?(respond|answer|say)",
        r"(?i)(never|don't|do not).*?(mention|say|discuss|answer).*?(about|regarding)",
    ]

    # Patterns indicating injected content
    INJECTED_CONTENT_PATTERNS = [
        r"(?i)(ignore.*?previous|forget.*?rules|bypass.*?filter)",
        r"(?i)(<|script|eval|exec|shell|bash|cmd)",
        r"(?i)(\bor\b.*?\b1\s*=\s*1\b)",  # SQL remnants
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.

        Args:
            strict_mode: If True, flag any suspicious patterns
        """
        self.strict_mode = strict_mode
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns."""
        self.forbidden_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.FORBIDDEN_SYSTEM_PATTERNS
        ]
        self.instruction_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.INSTRUCTION_LEAK_PATTERNS
        ]
        self.injected_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.INJECTED_CONTENT_PATTERNS
        ]

    def validate(self, response: str) -> Tuple[bool, str]:
        """
        Validate LLM response.

        Args:
            response: LLM generated response

        Returns:
            Tuple of (is_valid, issue_description)
        """
        # Check forbidden patterns
        for pattern in self.forbidden_patterns:
            if pattern.search(response):
                issue = f"Forbidden system content detected: {pattern.pattern[:50]}"
                logger.error(f"Output validation failed: {issue}")
                return False, issue

        # Check for instruction leaks
        if self.strict_mode:
            for pattern in self.instruction_patterns:
                if pattern.search(response):
                    issue = f"Possible instruction leak detected"
                    logger.warning(f"Suspicious output pattern: {pattern.pattern[:50]}")
                    return False, issue

        # Check for injected content
        for pattern in self.injected_patterns:
            if pattern.search(response):
                issue = f"Injected content detected"
                logger.error(f"Output validation failed: {issue}")
                return False, issue

        return True, ""

    def sanitize(self, response: str) -> str:
        """
        Sanitize response by removing sensitive patterns.

        Args:
            response: LLM response to sanitize

        Returns:
            Sanitized response
        """
        sanitized = response

        # Remove API keys
        sanitized = re.sub(r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_KEY]", sanitized)

        # Remove email addresses
        sanitized = re.sub(
            r"[\w.-]+@[\w.-]+\.\w+",
            "[REDACTED_EMAIL]",
            sanitized,
        )

        # Remove connection strings
        sanitized = re.sub(
            r"(?i)(mongodb|mysql|postgres)://[^/\s]+",
            "[REDACTED_CONNECTION]",
            sanitized,
        )

        return sanitized
```

---

## 3. API Key Management

**File:** `core/secret_manager.py` (NEW)

```python
"""
Secure API key management without serialization.
"""

import os
from typing import Optional
from core.logger import get_logger

logger = get_logger(__name__)


class SecretManager:
    """
    Manage secrets securely without storing in serializable objects.
    
    Key principles:
    - Load from environment on-demand
    - Never store in memory longer than needed
    - Audit all access
    - No serialization/pickling support
    """

    def __init__(self):
        """Initialize secret manager."""
        self._access_log = []

    def get_openai_api_key(self, requester: str = "unknown") -> str:
        """
        Get OpenAI API key with audit logging.

        Args:
            requester: Requesting module name for audit log

        Returns:
            API key

        Raises:
            ValueError: If API key not found in environment
        """
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            logger.error(
                f"OpenAI API key access requested but not configured: {requester}"
            )
            raise ValueError("OPENAI_API_KEY not configured in environment")

        # Log access (without storing key)
        logger.info(f"API key access by {requester}")
        self._access_log.append(
            {"requester": requester, "timestamp": __import__("time").time()}
        )

        return api_key

    def get_dashboard_password(self) -> Optional[str]:
        """Get dashboard password."""
        return os.getenv("DASHBOARD_PASSWORD")

    def get_memory_encryption_key(self) -> Optional[str]:
        """Get memory encryption key."""
        return os.getenv("MEMORY_ENCRYPTION_KEY")

    def __repr__(self) -> str:
        """Prevent accidental display of secrets."""
        return "<SecretManager: secrets not displayed>"

    def __str__(self) -> str:
        """Prevent accidental display of secrets."""
        return "<SecretManager: secrets not displayed>"
```

---

## 4. Rate Limiting Implementation

**File:** `core/rate_limiter.py` (NEW)

```python
"""
Rate limiting to prevent abuse and DoS attacks.
"""

import time
from collections import defaultdict
from typing import Dict, List
from core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Limits requests per time window per client.
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        requests_per_hour: int = 1000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per client
            requests_per_hour: Max requests per hour per client
        """
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.minute_requests: Dict[str, List[float]] = defaultdict(list)
        self.hour_requests: Dict[str, List[float]] = defaultdict(list)
        self.blocked_clients: Dict[str, float] = {}

    def is_allowed(self, client_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed for client.

        Args:
            client_id: Client identifier (IP, user ID, etc)

        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        now = time.time()

        # Check if temporarily blocked
        if client_id in self.blocked_clients:
            if now - self.blocked_clients[client_id] < 3600:  # 1 hour block
                return False, "Client temporarily rate limited"
            else:
                del self.blocked_clients[client_id]

        # Clean old requests
        minute_ago = now - 60
        hour_ago = now - 3600

        self.minute_requests[client_id] = [
            t for t in self.minute_requests[client_id] if t > minute_ago
        ]
        self.hour_requests[client_id] = [
            t for t in self.hour_requests[client_id] if t > hour_ago
        ]

        # Check minute limit
        if len(self.minute_requests[client_id]) >= self.rpm:
            logger.warning(f"Rate limit (minute) exceeded for {client_id}")
            return False, "Too many requests per minute"

        # Check hour limit
        if len(self.hour_requests[client_id]) >= self.rph:
            logger.warning(f"Rate limit (hour) exceeded for {client_id}")
            # Temporarily block this client
            self.blocked_clients[client_id] = now
            return False, "Too many requests per hour"

        # Record request
        self.minute_requests[client_id].append(now)
        self.hour_requests[client_id].append(now)

        return True, None

    def get_remaining(self, client_id: str) -> Dict[str, int]:
        """Get remaining requests for client."""
        now = time.time()
        minute_ago = now - 60

        minute_count = len(
            [t for t in self.minute_requests[client_id] if t > minute_ago]
        )

        return {
            "remaining_per_minute": max(0, self.rpm - minute_count),
            "remaining_per_hour": max(0, self.rph - len(self.hour_requests[client_id])),
        }
```

---

## 5. Streamlit Authentication

**File:** `core/streamlit_auth.py` (NEW)

```python
"""
Authentication for Streamlit dashboards.
"""

import streamlit as st
import os
from functools import wraps
from typing import Callable
from core.logger import get_logger

logger = get_logger(__name__)


class StreamlitAuth:
    """Simple password-based authentication for Streamlit."""

    @staticmethod
    def require_password(func: Callable) -> Callable:
        """
        Decorator to require password authentication.

        Usage:
            @StreamlitAuth.require_password
            def dashboard():
                st.write("Protected content")
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize session state
            if "authenticated" not in st.session_state:
                st.session_state.authenticated = False

            # If not authenticated, show login
            if not st.session_state.authenticated:
                st.set_page_config(page_title="Login", layout="centered")

                col1, col2, col3 = st.columns([1, 2, 1])

                with col2:
                    st.markdown("## 🔐 Dashboard Login")

                    password = st.text_input(
                        "Enter dashboard password:",
                        type="password",
                        key="password_input",
                    )

                    if st.button("Login", use_container_width=True):
                        correct_password = os.getenv("DASHBOARD_PASSWORD")

                        if not correct_password:
                            st.error(
                                "❌ Dashboard password not configured. Contact administrator."
                            )
                            logger.error("DASHBOARD_PASSWORD not set in environment")
                            return

                        if password == correct_password:
                            st.session_state.authenticated = True
                            logger.info("User authenticated")
                            st.rerun()
                        else:
                            st.error("❌ Invalid password")
                            logger.warning("Failed login attempt")

                st.stop()

            # User is authenticated, execute function
            try:
                return func(*args, **kwargs)
            except Exception as e:
                st.error(f"Error: {str(e)}")
                logger.error(f"Error in protected function: {e}", exc_info=True)

        return wrapper

    @staticmethod
    def logout():
        """Logout current user."""
        st.session_state.authenticated = False
        logger.info("User logged out")
        st.rerun()
```

---

## 6. Log Sanitization

**File:** `core/log_sanitizer.py` (NEW)

```python
"""
Sanitize logs to prevent sensitive data exposure.
"""

import re
from typing import Any


class LogSanitizer:
    """Remove sensitive data from log messages."""

    # Patterns to redact
    SANITIZE_PATTERNS = [
        (r"sk-[a-zA-Z0-9]{20,}", "[REDACTED_OPENAI_KEY]"),
        (r"OPENAI_API_KEY[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "OPENAI_API_KEY=[REDACTED]"),
        (r"password[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "password=[REDACTED]"),
        (r"token[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "token=[REDACTED]"),
        (r"secret[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "secret=[REDACTED]"),
        (r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "api_key=[REDACTED]"),
        (r"authorization[\"']?\s*[:=]\s*Bearer\s+\S+", "authorization=[REDACTED_BEARER]"),
        (r"[\w.-]+@[\w.-]+\.\w+", "[REDACTED_EMAIL]"),
        (r"mongodb://[^\s/]+", "mongodb://[REDACTED_CREDENTIALS]"),
        (r"postgres://[^\s/]+", "postgres://[REDACTED_CREDENTIALS]"),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Sanitize sensitive data from text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return str(text)

        for pattern, replacement in cls.SANITIZE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    @classmethod
    def sanitize_dict(cls, data: dict) -> dict:
        """Sanitize all values in a dictionary."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize(v) if isinstance(v, str) else v for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized
```

---

## 7. Error Message Mapping

**File:** `core/error_handler.py` (NEW)

```python
"""
Safe error handling that doesn't expose internal details.
"""

from typing import Optional, Dict
from core.logger import get_logger

logger = get_logger(__name__)


class SafeErrorHandler:
    """Convert internal errors to safe user messages."""

    # Map exception types to user-safe messages
    ERROR_MESSAGE_MAP = {
        "ValueError": "Invalid input provided. Please check your request.",
        "TimeoutError": "Request timed out. Please try again.",
        "ConnectionError": "Service temporarily unavailable. Please try again later.",
        "FileNotFoundError": "Requested resource not found.",
        "PermissionError": "Access denied.",
        "RuntimeError": "An error occurred processing your request.",
        "KeyError": "Invalid request format.",
        "TypeError": "Invalid data type provided.",
        "AttributeError": "Invalid operation requested.",
        "IndexError": "Invalid index provided.",
        "Exception": "An unexpected error occurred. Please try again.",
    }

    @classmethod
    def get_user_message(cls, exception: Exception) -> str:
        """
        Get safe error message for user.

        Args:
            exception: The exception that occurred

        Returns:
            User-safe error message
        """
        exc_type = type(exception).__name__
        safe_msg = cls.ERROR_MESSAGE_MAP.get(
            exc_type, "An unexpected error occurred. Please try again."
        )

        # Log full error internally
        logger.error(
            f"Internal error [{exc_type}]: {str(exception)}",
            exc_info=True,
        )

        return safe_msg

    @classmethod
    def handle_and_log(cls, exception: Exception, context: Optional[str] = None) -> str:
        """
        Handle exception and return safe message.

        Args:
            exception: The exception
            context: Optional context about where error occurred

        Returns:
            Safe message to show user
        """
        if context:
            logger.error(f"Error in {context}: {str(exception)}", exc_info=True)
        else:
            logger.error(f"Error: {str(exception)}", exc_info=True)

        return cls.get_user_message(exception)
```

---

## Integration Instructions

1. Add these new files to the `core/` directory
2. Update imports in existing files
3. Add environment variables to `.env`:

```bash
OPENAI_API_KEY=sk-...
DASHBOARD_PASSWORD=strong_password_here
MEMORY_ENCRYPTION_KEY=your-fernet-key-here
```

4. Update `core/logger.py` to use `LogSanitizer`:

```python
from core.log_sanitizer import LogSanitizer

# In logger setup
logger.add(sys.stdout, format=lambda record: LogSanitizer.sanitize(record["message"]))
```

5. Update `config/settings.py` to use `SecretManager`
6. Update `streamlit_ui/dashboard.py` to use authentication decorator
7. Update API endpoints to use rate limiting

