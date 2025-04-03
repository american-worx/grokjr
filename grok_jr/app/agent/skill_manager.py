# In app/agent/skill_manager.py

import json
import logging
import sqlite3
import subprocess
import os
import re
import resource
import sys
import tempfile
from textwrap import dedent
import venv
from io import StringIO
from datetime import datetime
from grok_jr.app.memory.sqlite_store import SQLiteStore
from qdrant_client.models import Filter, FieldCondition, MatchValue  # Add these imports
from grok_jr.app.memory.qdrant_store import QdrantStore
from grok_jr.app.models.skill import Skill
from grok_jr.app.agent.ethics_manager import EthicsManager
from grok_jr.app.dependencies import get_inference_engine, get_qdrant_store_skills
import logging
from grok_jr.app.config.system_dependencies import SYSTEM_DEPENDENCIES  # New import

logger = logging.getLogger(__name__)

class SkillManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sqlite_store = SQLiteStore()
        self.qdrant_store = get_qdrant_store_skills()
        self.ethics_manager = EthicsManager()
        self.inference_engine = get_inference_engine()
        self.scripts_dir = "skill_scripts"  # Optional for file-based skills
        os.makedirs(self.scripts_dir, exist_ok=True)
        self.venv_dir = "grok_jr_venv"
        self._setup_venv()

    def _setup_venv(self):
        """Set up the virtual environment if it doesn't exist."""
        if not os.path.exists(self.venv_dir):
            self.logger.info(f"Creating virtual environment at '{self.venv_dir}'...")
            try:
                venv_builder = venv.EnvBuilder(with_pip=True)
                venv_builder.create(self.venv_dir)
                self.logger.info(f"Virtual environment created at '{self.venv_dir}'.")
            except Exception as e:
                self.logger.error(f"Failed to create virtual environment: {str(e)}")
                raise RuntimeError(f"Cannot proceed without venv: {str(e)}")
        
        self.venv_python = os.path.join(self.venv_dir, "bin" if os.name != "nt" else "Scripts", "python")
        self.venv_pip = os.path.join(self.venv_dir, "bin" if os.name != "nt" else "Scripts", "pip")
        # Ensure pip is up-to-date
        try:
            subprocess.run([self.venv_pip, "install", "--upgrade", "pip"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to upgrade pip: {e.stderr}")

    def _has_placeholder_comments(self, code: str) -> bool:
        placeholder_patterns = [
            r'#\s*Add logic',
            r'#\s*Implement',
            r'#\s*TODO',
            r'#\s*Complete',
        ]
        for line in code.splitlines():
            line = line.strip()
            for pattern in placeholder_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    return True
        return False

    def _detect_dependencies(self, code: str) -> list:
        """Detect external Python dependencies, excluding system modules."""
        dependencies = set()
        import_pattern = r'^(?:import|from)\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)'
        for line in code.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            match = re.match(import_pattern, line)
            if match:
                module = match.group(1).split('.')[0]
                if module not in SYSTEM_DEPENDENCIES:
                    dependencies.add(module)
        return list(dependencies)

    def _get_installed_packages(self) -> set:
        """Get list of installed packages in the venv."""
        try:
            result = subprocess.run(
                [self.venv_pip, "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True
            )
            return {line.split('==')[0].lower() for line in result.stdout.splitlines()}
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to list installed packages: {e.stderr}")
            raise

    def _install_dependencies(self, dependencies: list) -> bool:
        """Install missing dependencies in the venv."""
        try:
            installed = self._get_installed_packages()
            missing = [dep for dep in dependencies if dep.lower() not in installed]
            if missing:
                self.logger.info(f"Installing missing dependencies: {missing}")
                result = subprocess.run(
                    [self.venv_pip, "install"] + missing,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.logger.info(f"Installed dependencies: {missing}, Output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies: {e.stderr}")
            return False

    # In app/agent/skill_manager.py

    def search_skill(self, skill_name: str) -> Skill | None:
        self.logger.info(f"Searching for skill '{skill_name}' in local storage...")
        skill_data = self.sqlite_store.get_skill(skill_name)
        if skill_data:
            self.logger.info(f"Found skill '{skill_name}' in local storage.")
            return Skill(**skill_data)

        self.logger.info(f"Skill '{skill_name}' not found locally. Querying xAI API or local model...")
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                prompt = (
                    f"Provide detailed instructions and fully implemented Python code for the skill '{skill_name}' "
                    "in a structured format. Ensure the code is complete, functional, and does not contain placeholder "
                    "comments like '# Add logic' or '# TODO'. Include all necessary logic to make the code executable. "
                    "Execute the task directly without generating additional files unless explicitly required. "
                    "Include a main(params) function that accepts a dictionary of parameters and prints the result. "
                    "Use the params dictionary to access any input values provided, avoiding hardcoded values where possible. "
                    "If the skill requires root privileges (e.g., network operations), include a check using os.geteuid() == 0 "
                    "and provide a fallback message if not running as root. Ensure all required modules (e.g., os, scapy) are imported. "
                    "Set a reasonable timeout (e.g., 5 seconds) for network operations to ensure responses are captured."
                )
                local_response, xai_response = self.inference_engine.predict(prompt, use_xai_api=True)
                instructions = xai_response
                code_match = re.search(r'```python\n(.*?)```', xai_response, re.DOTALL)
                code = code_match.group(1).strip() if code_match else None
                if not code:
                    self.logger.warning(f"No code found in response for skill '{skill_name}' on attempt {attempt + 1}.")
                    continue

                if self._has_placeholder_comments(code):
                    self.logger.warning(f"Incomplete code detected for skill '{skill_name}' on attempt {attempt + 1}.")
                    continue

                skill = Skill(name=skill_name, instructions=instructions, code=code)
                self.acquire_skill(skill)
                self.logger.info(f"Acquired skill '{skill_name}'.")
                return skill
            except Exception as e:
                self.logger.error(f"Failed to acquire skill '{skill_name}' on attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts - 1:
                    return None
                continue
        return None

    def acquire_skill(self, skill: Skill):
        self.logger.info(f"Acquiring skill '{skill.name}'...")
        existing_skill = self.sqlite_store.get_skill(skill.name)
        if existing_skill:
            self.logger.info(f"Skill '{skill.name}' already exists. Updating existing entry.")
            skill_dict = skill.dict()
            skill_dict["id"] = existing_skill["id"]
            skill_dict["timestamp"] = skill_dict["timestamp"].isoformat()
            self.sqlite_store.update_skill(skill_dict)
        else:
            skill_dict = skill.dict()
            skill_dict["timestamp"] = skill_dict["timestamp"].isoformat()
            skill_id = self.sqlite_store.add_skill(skill_dict)
            skill_dict["id"] = skill_id
        embedding_text = f"{skill.name}: {skill.instructions}"
        self.qdrant_store.add_embedding(embedding_text, skill_dict)

    def get_skill(self, skill_name: str) -> Skill | None:
        skill_data = self.sqlite_store.get_skill(skill_name)
        if skill_data:
            return Skill(**skill_data)
        return None
    

    def delete_skill(self, skill_name: str) -> str:
        """Delete a skill by name from both SQLite and Qdrant."""
        skill = self.get_skill(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found in the database."
        
        # Delete from SQLite
        self.sqlite_store.delete_skill(skill_name)
        
        # Delete from Qdrant using modern API
        self.qdrant_store.client.delete(
            collection_name="skills",
            points_selector=Filter(
                must=[FieldCondition(key="name", match=MatchValue(value=skill_name))]
            )
        )
        self.logger.info(f"Deleted skill '{skill_name}' from SQLite and Qdrant.")
        return f"Successfully deleted skill '{skill_name}'."
    
    def update_skill(self, skill_name: str, new_instructions: str = None, new_code: str = None) -> str:
        """Update a skill by name with new instructions and/or code."""
        skill = self.get_skill(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found in the database."
        
        updated_skill = Skill(
            name=skill_name,
            instructions=new_instructions or skill.instructions,
            code=new_code or skill.code,
            timestamp=datetime.now()
        )
        skill_dict = updated_skill.dict()
        skill_dict["id"] = skill.id
        skill_dict["timestamp"] = skill_dict["timestamp"].isoformat()
        self.sqlite_store.update_skill(skill_dict)
        embedding_text = f"{skill_name}: {updated_skill.instructions}"
        self.qdrant_store.add_embedding(embedding_text, skill_dict)
        self.logger.info(f"Updated skill '{skill_name}'.")
        return f"Successfully updated skill '{skill_name}'."

    def list_skills(self) -> str:
        """List all skills stored in the database."""
        conn = sqlite3.connect(self.sqlite_store.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM skills")
        skills = cursor.fetchall()
        conn.close()

        if not skills:
            return "No skills found in the database."
        
        skill_names = [skill[0] for skill in skills]
        return "Available skills: " + ", ".join(skill_names)
    
    def apply(self, skill: Skill, user_permission: bool = False, ethics_approved: bool = False, params: dict = None) -> str:
        if not ethics_approved:
            is_safe, message = self.ethics_manager.validate_skill(skill)
            if "Warning:" in message:
                return f"ETHICS_WARNING:{message}"

        if self.ethics_manager.requires_permission(skill) and not user_permission:
            self.logger.info(f"Skill '{skill.name}' requires user permission before execution.")
            return f"PERMISSION_REQUIRED:Skill '{skill.name}' requires your permission to execute. Please confirm."

        if not skill.code:
            self.logger.warning(f"Skill '{skill.name}' has no code to execute.")
            return "No code available to execute for this skill."

        self.logger.info(f"Applying skill '{skill.name}' in isolated venv with params: {params}...")
        try:
            dependencies = self._detect_dependencies(skill.code)
            self.logger.info(f"Detected dependencies for skill '{skill.name}': {dependencies}")
            if dependencies and not self._install_dependencies(dependencies):
                return f"Skill execution failed: Could not install dependencies {dependencies}. Please check logs for details."

            params_json = json.dumps(params or {})
            script_code = (
                "import sys\n"
                "import json\n\n" +
                skill.code + "\n\n" +
                f"params = json.loads('{params_json}')\n"
                "main(params)\n"
            )
            self.logger.debug(f"Script code to execute:\n{script_code}")

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
                temp_file.write(script_code)
                temp_file_path = temp_file.name

            try:
                process = subprocess.run(
                    ["sudo", self.venv_python, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                self.logger.debug(f"Subprocess stdout: {process.stdout}")
                self.logger.debug(f"Subprocess stderr: {process.stderr}")

                if process.returncode != 0:
                    self.logger.error(f"Skill execution failed: {process.stderr}")
                    return f"Skill execution failed: {process.stderr}"

                output = process.stdout.strip()
                self.logger.info(f"Skill '{skill.name}' executed successfully: {output}")
                return output if output else "Skill executed with no output."
            finally:
                os.unlink(temp_file_path)
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Skill execution timed out: {str(e)}")
            return f"Skill execution failed: Timed out after 30 seconds."
        except Exception as e:
            self.logger.error(f"Failed to apply skill '{skill.name}': {str(e)}")
            return f"Failed to apply skill: {str(e)}"

    def improve(self, skill: Skill, feedback: str) -> Skill:
        self.logger.info(f"Improving skill '{skill.name}' with feedback: {feedback}")
        try:
            prompt = (
                f"Improve the skill '{skill.name}' with the following feedback: {feedback}. "
                f"Current instructions: {skill.instructions}. Current code: {skill.code}. "
                "Ensure the improved code is fully implemented, functional, and does not contain placeholder "
                "comments like '# Add logic' or '# TODO'. Include all necessary logic to make the code executable. "
                "Include a main(params) function that accepts a dictionary of parameters and prints the result."
            )
            local_response, xai_response = self.inference_engine.predict(prompt, use_xai_api=True)
            improved_instructions = xai_response
            code_match = re.search(r'```python\n(.*?)```', xai_response, re.DOTALL)
            improved_code = code_match.group(1).strip() if code_match else skill.code
            if not improved_code:
                self.logger.warning(f"No code found in response for improved skill '{skill.name}'.")
                improved_code = skill.code

            if self._has_placeholder_comments(improved_code):
                self.logger.warning(f"Incomplete code detected in improved skill '{skill.name}'. Using original code.")
                improved_code = skill.code

            improved_skill = Skill(
                name=skill.name,
                instructions=improved_instructions,
                code=improved_code,
                timestamp=datetime.now()
            )
            self.acquire_skill(improved_skill)
            self.logger.info(f"Improved skill '{skill.name}'.")
            return improved_skill
        except Exception as e:
            self.logger.error(f"Failed to improve skill '{skill.name}': {str(e)}")
            return skill