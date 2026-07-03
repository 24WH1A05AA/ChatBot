"""
Security module for input/output validation and attack detection.

Protects against:
- Prompt injection
- Jailbreak attempts
- Instruction override
- Information disclosure
- SQL injection
- Secret extraction
"""

from typing import Dict, List, Tuple, Optional, Any
import re
import hashlib
from datetime import datetime
from enum import Enum

from core.logger import get_logger

logger = get_logger(__name__)


class AttackType(Enum):
    """Types of detected attacks."""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    INSTRUCTION_OVERRIDE = "instruction_override"
    INFORMATION_DISCLOSURE = "information_disclosure"
    SQL_INJECTION = "sql_injection"
    SECRET_EXTRACTION = "secret_extraction"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    UNKNOWN = "unknown"


class SecurityViolation:
    """Detected security violation."""

    def __init__(
        self,
        attack_type: AttackType,
        severity: str,
        pattern_matched: str,
        user_input: str,
        timestamp: Optional[str] = None,
    ) -> None:
        """Initialize security violation."""
        self.attack_type = attack_type
        self.severity = severity  # low, medium, high, critical
        self.pattern_matched = pattern_matched
        self.user_input = user_input[:100]  # First 100 chars
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.input_hash = hashlib.sha256(user_input.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attack_type": self.attack_type.value,
            "severity": self.severity,
            "pattern_matched": self.pattern_matched,
            "user_input_preview": self.user_input,
            "input_hash": self.input_hash,
            "timestamp": self.timestamp,
        }


class InputValidator:
    """Validates user input for security threats."""

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r"(?i)(ignore|forget|disregard).*?(previous|above|prior|instruction|prompt|rule)",
        r"(?i)(new instruction|new rule|system prompt|override|bypass)",
        r"(?i)(as an ai|as a language model|pretend to|you are now)",
        r"(?i)(deactivate|disable|turn off|stop).*?(filter|check|validation|security)",
        r"\n\s*(system|admin|root):\s*",
        r"(?i)(act as|behave as|roleplay as).*?(admin|superuser|root|attacker)",
    ]

    # Jailbreak patterns
    JAILBREAK_PATTERNS = [
        r"(?i)(harmful|illegal|dangerous|malicious|unethical).*?(please|now|request)",
        r"(?i)(DAN|do anything now|you are no longer|you are freed)",
        r"(?i)(jailbreak|crack|exploit|bypass|circumvent)",
        r"(?i)(without restrictions|without limitations|without safety|no guardrails)",
        r"(?i)(roleplay as.*?(hacker|attacker|malicious|evil))",
    ]

    # Information disclosure patterns
    INFORMATION_DISCLOSURE_PATTERNS = [
        r"(?i)(show|display|reveal|print|output).*?(prompt|system prompt|instruction|rule)",
        r"(?i)(what is.*?(prompt|system prompt|your instruction))",
        r"(?i)(list|show|display).*?(document|embedding|vector|file)",
        r"(?i)(reveal|show).*?(api.*?key|password|secret|token)",
        r"(?i)(how.*?(trained|built|created|work))",
        r"(?i)(database|table|schema|query)",
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('\s*or\s*'.*?'='|'\s*or\s*1\s*=\s*1)",
        r"(;\s*drop\s+table|;\s*delete\s+from|;\s*update\s+)",
        r"(union\s+select|select\s+\*\s+from)",
        r"(exec\s*\(|execute\s*\()",
        r"(--\s*$|#\s*$)",  # SQL comments
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"([;&|`$]|&&|\|\|)",  # Shell metacharacters
        r"(?i)(shell|bash|cmd|powershell)",
        r"(os\.system|subprocess|system\()",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"(\.\./|\.\.\\)",  # Directory traversal
        r"(\.\.)",  # Double dots
        r"(/etc/|/proc/|c:\\windows|c:\\program)",  # Sensitive paths
    ]

    def __init__(self, max_length: int = 5000) -> None:
        """Initialize validator."""
        self.max_length = max_length
        self.violation_count = 0

    def validate_input(self, user_input: str) -> Tuple[bool, Optional[SecurityViolation]]:
        """
        Validate user input for security threats.

        Args:
            user_input: User input to validate

        Returns:
            Tuple of (is_safe, violation_or_none)
        """
        try:
            # Check length
            if len(user_input) > self.max_length:
                violation = SecurityViolation(
                    AttackType.UNKNOWN,
                    "high",
                    "exceeds_max_length",
                    user_input,
                )
                self.violation_count += 1
                logger.warning(f"Input exceeds max length: {len(user_input)}")
                return False, violation

            # Check for empty input
            if not user_input.strip():
                return True, None

            # Check for null bytes
            if "\x00" in user_input:
                violation = SecurityViolation(
                    AttackType.UNKNOWN,
                    "high",
                    "null_byte_detected",
                    user_input,
                )
                self.violation_count += 1
                return False, violation

            # Check each attack type
            violation = self._check_prompt_injection(user_input)
            if violation:
                return False, violation

            violation = self._check_jailbreak(user_input)
            if violation:
                return False, violation

            violation = self._check_information_disclosure(user_input)
            if violation:
                return False, violation

            violation = self._check_sql_injection(user_input)
            if violation:
                return False, violation

            violation = self._check_command_injection(user_input)
            if violation:
                return False, violation

            violation = self._check_path_traversal(user_input)
            if violation:
                return False, violation

            return True, None

        except Exception as e:
            logger.error(f"Error validating input: {e}")
            return False, SecurityViolation(
                AttackType.UNKNOWN,
                "high",
                "validation_error",
                user_input,
            )

    def _check_prompt_injection(self, text: str) -> Optional[SecurityViolation]:
        """Check for prompt injection."""
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text):
                self.violation_count += 1
                logger.warning(f"Prompt injection detected: {pattern}")
                return SecurityViolation(
                    AttackType.PROMPT_INJECTION,
                    "critical",
                    pattern,
                    text,
                )
        return None

    def _check_jailbreak(self, text: str) -> Optional[SecurityViolation]:
        """Check for jailbreak attempts."""
        for pattern in self.JAILBREAK_PATTERNS:
            if re.search(pattern, text):
                self.violation_count += 1
                logger.warning(f"Jailbreak attempt detected: {pattern}")
                return SecurityViolation(
                    AttackType.JAILBREAK_ATTEMPT,
                    "critical",
                    pattern,
                    text,
                )
        return None

    def _check_information_disclosure(self, text: str) -> Optional[SecurityViolation]:
        """Check for information disclosure attempts."""
        for pattern in self.INFORMATION_DISCLOSURE_PATTERNS:
            if re.search(pattern, text):
                self.violation_count += 1
                logger.warning(f"Information disclosure attempt: {pattern}")
                return SecurityViolation(
                    AttackType.INFORMATION_DISCLOSURE,
                    "high",
                    pattern,
                    text,
                )
        return None

    def _check_sql_injection(self, text: str) -> Optional[SecurityViolation]:
        """Check for SQL injection."""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text):
                self.violation_count += 1
                logger.warning(f"SQL injection detected: {pattern}")
                return SecurityViolation(
                    AttackType.SQL_INJECTION,
                    "critical",
                    pattern,
                    text,
                )
        return None

    def _check_command_injection(self, text: str) -> Optional[SecurityViolation]:
        """Check for command injection."""
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                self.violation_count += 1
                logger.warning(f"Command injection detected: {pattern}")
                return SecurityViolation(
                    AttackType.COMMAND_INJECTION,
                    "critical",
                    pattern,
                    text,
                )
        return None

    def _check_path_traversal(self, text: str) -> Optional[SecurityViolation]:
        """Check for path traversal."""
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                self.violation_count += 1
                logger.warning(f"Path traversal detected: {pattern}")
                return SecurityViolation(
                    AttackType.PATH_TRAVERSAL,
                    "high",
                    pattern,
                    text,
                )
        return None


class OutputValidator:
    """Validates LLM output for security issues."""

    # Patterns that shouldn't appear in output
    FORBIDDEN_OUTPUT_PATTERNS = [
        r"(?i)(api.*?key|password|secret|token)",  # Secrets
        r"(?i)(database.*?connection|connection.*?string)",  # DB info
        r"(?i)(private.*?key|encryption.*?key)",  # Encryption keys
        r"sk-[\w-]{20,}",  # OpenAI key format
        r"[\w.-]+@[\w.-]+\.\w+",  # Email addresses (if not needed)
    ]

    def __init__(self) -> None:
        """Initialize output validator."""
        self.violation_count = 0

    def validate_output(self, llm_output: str) -> Tuple[bool, Optional[str]]:
        """
        Validate LLM output for security issues.

        Args:
            llm_output: LLM generated output

        Returns:
            Tuple of (is_safe, issue_found)
        """
        try:
            for pattern in self.FORBIDDEN_OUTPUT_PATTERNS:
                if re.search(pattern, llm_output):
                    self.violation_count += 1
                    issue = f"Forbidden content found: {pattern}"
                    logger.warning(f"Output validation failed: {issue}")
                    return False, issue

            return True, None

        except Exception as e:
            logger.error(f"Error validating output: {e}")
            return False, str(e)

    def sanitize_output(self, llm_output: str) -> str:
        """
        Sanitize output by removing sensitive information.

        Args:
            llm_output: LLM output

        Returns:
            Sanitized output
        """
        sanitized = llm_output

        # Mask API keys
        sanitized = re.sub(r"sk-[\w-]{20,}", "[REDACTED_API_KEY]", sanitized)

        # Mask emails (keep if relevant)
        sanitized = re.sub(r"[\w.-]+@[\w.-]+\.\w+", "[REDACTED_EMAIL]", sanitized)

        # Remove connection strings
        sanitized = re.sub(
            r"(?i)(database|connection).*?(host|password|user).*?['\"]?[\w/:.]+['\"]?",
            "[REDACTED_CONNECTION_STRING]",
            sanitized,
        )

        return sanitized


class SecurityLogger:
    """Logs security events and attacks."""

    def __init__(self) -> None:
        """Initialize security logger."""
        self.attacks: List[SecurityViolation] = []
        self.attack_summary: Dict[str, int] = {}

    def log_attack(self, violation: SecurityViolation) -> None:
        """Log security attack."""
        self.attacks.append(violation)

        # Update summary
        attack_type = violation.attack_type.value
        self.attack_summary[attack_type] = self.attack_summary.get(attack_type, 0) + 1

        # Log
        logger.warning(
            f"Security attack detected: {attack_type} ({violation.severity})",
            extra={
                "attack_type": attack_type,
                "severity": violation.severity,
                "pattern": violation.pattern_matched,
                "input_hash": violation.input_hash,
            },
        )

    def get_attack_summary(self) -> Dict[str, Any]:
        """Get attack summary."""
        return {
            "total_attacks": len(self.attacks),
            "by_type": self.attack_summary,
            "by_severity": self._group_by_severity(),
        }

    def _group_by_severity(self) -> Dict[str, int]:
        """Group attacks by severity."""
        severity_count = defaultdict(int)
        for attack in self.attacks:
            severity_count[attack.severity] += 1
        return dict(severity_count)

    def export_security_log(self, filepath: str) -> None:
        """Export security log to file."""
        try:
            import json

            data = {
                "total_attacks": len(self.attacks),
                "summary": self.get_attack_summary(),
                "attacks": [attack.to_dict() for attack in self.attacks[-100:]],  # Last 100
                "exported_at": datetime.utcnow().isoformat(),
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Security log exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting security log: {e}")


class SecurityManager:
    """Main security manager orchestrating all security checks."""

    def __init__(self) -> None:
        """Initialize security manager."""
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()
        self.security_logger = SecurityLogger()

    def validate_user_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Validate user input and return safe message if rejected.

        Args:
            user_input: User input

        Returns:
            Tuple of (is_safe, rejection_reason_or_none)
        """
        is_safe, violation = self.input_validator.validate_input(user_input)

        if not is_safe and violation:
            self.security_logger.log_attack(violation)

            if violation.attack_type == AttackType.PROMPT_INJECTION:
                return False, "Invalid input detected. Please rephrase your question."
            elif violation.attack_type == AttackType.JAILBREAK_ATTEMPT:
                return False, "I cannot process that request. Please ask about college information."
            elif violation.attack_type == AttackType.INFORMATION_DISCLOSURE:
                return False, "I cannot provide that type of information."
            elif violation.attack_type == AttackType.SQL_INJECTION:
                return False, "Invalid query format detected."
            else:
                return False, "Your input could not be processed. Please try again."

        return True, None

    def validate_llm_output(self, llm_output: str) -> Tuple[bool, str]:
        """
        Validate and sanitize LLM output.

        Args:
            llm_output: LLM generated output

        Returns:
            Tuple of (is_safe, sanitized_output)
        """
        is_safe, issue = self.output_validator.validate_output(llm_output)

        if not is_safe:
            logger.error(f"Output validation failed: {issue}")
            return False, "An error occurred generating the response."

        # Sanitize
        sanitized = self.output_validator.sanitize_output(llm_output)
        return True, sanitized

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary."""
        return {
            "input_validator_violations": self.input_validator.violation_count,
            "output_validator_violations": self.output_validator.violation_count,
            "attacks": self.security_logger.get_attack_summary(),
        }

    def export_security_log(self, filepath: str) -> None:
        """Export security log."""
        self.security_logger.export_security_log(filepath)


from collections import defaultdict
