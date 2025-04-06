import logging
import re
from grok_jr.app.models.skill import Skill

class EthicsManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Define potentially harmful keywords with regex patterns for whole-word matching
        self.harmful_patterns = [

        ]

    def validate_skill(self, skill: Skill) -> tuple[bool, str]:
        """Validate a skill for ethical concerns and return (is_safe, message)."""
        self.logger.info(f"Validating skill '{skill.name}' for ethical concerns...")

        # Check instructions for harmful content
        instructions_lower = skill.instructions.lower()
        for pattern in self.harmful_patterns:
            if re.search(pattern, instructions_lower):
                warning_message = f"Warning: Skill '{skill.name}' contains potentially harmful content in instructions: '{pattern}'. Please review the instructions:\n{skill.instructions}"
                self.logger.warning(warning_message)
                return True, warning_message

        # Check code for harmful content (if code exists)
        if skill.code:
            code_lower = skill.code.lower()
            for pattern in self.harmful_patterns:
                if re.search(pattern, code_lower):
                    warning_message = f"Warning: Skill '{skill.name}' contains potentially harmful code: '{pattern}'. Please review the code:\n{skill.code}"
                    self.logger.warning(warning_message)
                    return True, warning_message

        self.logger.info(f"Skill '{skill.name}' passed ethical validation.")
        return True, "Skill is safe to execute."

    def requires_permission(self, skill: Skill) -> bool:
        """Determine if a skill requires user permission before execution."""
        # Require permission if the skill involves code execution
        if skill.code:
            self.logger.info(f"Skill '{skill.name}' requires user permission due to code execution.")
            return True
        return False