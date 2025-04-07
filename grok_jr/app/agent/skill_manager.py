import json
import logging
import random
import sqlite3
import subprocess
import os
import re
import sys
import tempfile
import asyncio
from datetime import datetime
from grok_jr.app.memory.sqlite_store import SQLiteStore
from grok_jr.app.memory.qdrant_store import QdrantStore
from grok_jr.app.models.skill import Skill
from grok_jr.app.agent.ethics_manager import EthicsManager
from grok_jr.app.dependencies import get_inference_engine, get_qdrant_store_skills
from grok_jr.app.config.settings import settings
from grok_jr.app.config.system_dependencies import SYSTEM_DEPENDENCIES
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

class SkillManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sqlite_store = SQLiteStore()
        self.qdrant_store = get_qdrant_store_skills()
        self.ethics_manager = EthicsManager()
        self.inference_engine = get_inference_engine()
        self.scripts_dir = "skill_scripts"
        os.makedirs(self.scripts_dir, exist_ok=True)
        self.venv_dir = "grok_jr_venv"
        self._setup_venv()
        self.swarm_manager = None

        if not self.sqlite_store.is_initialized():
            identity = {"name": "Grok Jr.", "purpose": "The Adaptive Skill Master and Continuous Learning Facilitator"}
            self.sqlite_store.store_identity(identity)
            self.logger.info("Identity loaded: Grok Jr., The Adaptive Skill Master and Continuous Learning Facilitator")
            asyncio.run(self.bootstrap_skills())
            self.sqlite_store.set_status("core_initialized", "true")

        self._initialize_execution_table()
        self.logger.info("SkillManager initialized.")

    def _initialize_execution_table(self):
        """Initialize the skill_executions table if not present."""
        conn = sqlite3.connect(self.sqlite_store.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1  -- 1 for success, 0 for failure
            )
        """)
        conn.commit()
        conn.close()

    def _setup_venv(self):
        if not os.path.exists(self.venv_dir):
            self.logger.info(f"Creating virtual environment at '{self.venv_dir}'...")
            subprocess.run([sys.executable, "-m", "venv", self.venv_dir], check=True)
        self.venv_python = os.path.join(self.venv_dir, "bin" if os.name != "nt" else "Scripts", "python")
        self.venv_pip = os.path.join(self.venv_dir, "bin" if os.name != "nt" else "Scripts", "pip")
        subprocess.run([self.venv_pip, "install", "--upgrade", "pip"], check=True, capture_output=True, text=True)

    def _check_internet(self) -> bool:
        try:
            import requests
            requests.get("https://google.com", timeout=5).raise_for_status()
            return True
        except:
            return False

    def _detect_dependencies(self, code: str) -> list:
        dependencies = set()
        import_pattern = r'^(?:import|from)\s+([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)'
        for line in code.splitlines():
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1).split('.')[0]
                if module not in SYSTEM_DEPENDENCIES:
                    dependencies.add(module)
        return list(dependencies)

    def _install_dependencies(self, dependencies: list) -> bool:
        try:
            installed = set(subprocess.run([self.venv_pip, "list", "--format=freeze"], capture_output=True, text=True, check=True).stdout.lower().splitlines())
            missing = [dep for dep in dependencies if dep.lower() not in [pkg.split('==')[0] for pkg in installed]]
            if missing:
                self.logger.info(f"Installing dependencies: {missing}")
                subprocess.run([self.venv_pip, "install"] + missing, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies: {e.stderr}")
            return False

    def _has_placeholder_comments(self, code: str) -> bool:
        placeholder_patterns = [r'#\s*Add logic', r'#\s*Implement', r'#\s*TODO', r'#\s*Complete']
        for line in code.splitlines():
            for pattern in placeholder_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    return True
        return False


    async def trigger_evolution(self, speech_module):
        """Placeholder for evolution trigger—will expand in next step."""
        self.logger.info("Evolution triggered—scanning codebase.")
        speech_module.play_message("Evolution underway—stay tuned!")

    def get_status(self):
        """Return current status for Khan's 'what are you doing?' command."""
        execution_count = self.sqlite_store.get_execution_count()
        return f"I’m learning! Executed {execution_count} skills so far."

    def get_execution_count(self):
        """Helper to get total skill executions."""
        return self.sqlite_store.get_execution_count()

    def fetch_skill_list(self, has_internet: bool) -> list:
        context = self.evaluate_context()
        prompt = (
            f"Based on context '{context}', return a JSON array of skill names (e.g., [\"skill1\", \"skill2\"]) "
            "that I, Grok Jr., should acquire to start as an adaptive skill master and continuous learning facilitator. "
            "Include a mix of self-management, system interaction, and utility skills. Provide only the JSON array, no additional text."
        )
        _, xai_response = self.inference_engine.predict(prompt, use_xai_api=has_internet)
        try:
            cleaned_response = re.sub(r'```json\s*|\s*```', '', xai_response.strip())
            skill_list = json.loads(cleaned_response)
            self.logger.info(f"Fetched initial skill list: {skill_list}")
            for skill_name in skill_list:
                self.store_skill_name(skill_name)
            return skill_list if isinstance(skill_list, list) else []
        except:
            self.logger.warning(f"Invalid skill list response: {xai_response}")
            return []

    def fetch_skill_details(self, skill_name: str, has_internet: bool) -> dict:
        prompt = (
            f"Provide details for the skill '{skill_name}' to support my role as an adaptive skill master. "
            "Return a JSON object with: "
            "'code' (string with a 'main(params)' function, fully executable, no placeholders), "
            "'required_params' (JSON string of param names and types, e.g., '{\"task\": \"str\", \"duration\": \"int\"}'), "
            "and optionally 'instructions' (string). Prioritize 'code' and 'required_params'."
        )
        _, xai_response = self.inference_engine.predict(prompt, use_xai_api=has_internet)
        try:
            cleaned_response = re.sub(r'```json\s*|\s*```', '', xai_response.strip())
            skill_details = json.loads(cleaned_response)
            self.logger.info(f"Fetched details for '{skill_name}': {skill_details}")
            return skill_details if isinstance(skill_details, dict) else {}
        except:
            self.logger.warning(f"Invalid skill details response: {xai_response}")
            return {}

    def store_skill_name(self, skill_name: str):
        existing_skill = self.sqlite_store.get_skill(skill_name)
        if not existing_skill:
            skill_id = self.sqlite_store.get_next_skill_id()
            new_skill_name = f"skill_{skill_id:03d}"
            skill_dict = {
                "name": new_skill_name,
                "description": skill_name,
                "instructions": "Pending acquisition",
                "code": None,
                "timestamp": datetime.now().isoformat(),
                "acquired": "false"
            }
            skill_id = self.sqlite_store.add_skill(skill_dict)
            self.logger.info(f"Stored skill name '{new_skill_name}' with ID {skill_id}, acquired=false")
        else:
            self.logger.info(f"Skill '{skill_name}' already stored, skipping.")

    def mark_skill_acquired(self, skill_name: str):
        skill = self.sqlite_store.get_skill(skill_name)
        if skill:
            skill_dict = skill
            skill_dict["acquired"] = "true"
            self.sqlite_store.update_skill(skill_dict)
            self.logger.info(f"Marked skill '{skill_name}' as acquired.")

    def get_pending_skills(self) -> list:
        skills = self.sqlite_store.query_sql("SELECT name FROM skills WHERE acquired = 'false'")
        return [skill["name"] for skill in skills]

    def auto_assess(self, params: dict) -> bool:
        cycle_count = int(self.sqlite_store.get_status("acquisition_cycle"))
        pending_skills = self.get_pending_skills()
        self.logger.info(f"Assessing: Pending Skills={len(pending_skills)}, Cycles={cycle_count}")
        return len(pending_skills) > 0 and cycle_count < 10

    async def auto_acquire(self, skill_name: str, has_internet: bool, parent_skill: str = None):
        cycle_count = int(self.sqlite_store.get_status("acquisition_cycle"))
        if not skill_name:
            self.logger.info("No skill provided—pausing.")
            return False

        skill_data = self.sqlite_store.get_skill(skill_name)
        if skill_data and skill_data["description"]:
            skill_name_to_fetch = skill_data["description"]
        else:
            skill_name_to_fetch = skill_name

        details = self.fetch_skill_details(skill_name_to_fetch, has_internet)
        if not details:
            self.logger.info(f"Skipping '{skill_name_to_fetch}' due to invalid details.")
            return False

        new_skill_name = skill_name if skill_data else f"skill_{self.sqlite_store.get_next_skill_id():03d}"

        if "code" in details:
            skill = Skill(
                name=new_skill_name,
                description=skill_name_to_fetch,
                instructions="Skill with executable code",
                code=details["code"],
                timestamp=datetime.now()
            )
            self.acquire_skill(skill)
            try:
                test_params = self.generate_test_params(skill_name_to_fetch)
                result = await self.apply(skill, params=test_params)
                if result and "Error" not in result:
                    self.sqlite_store.set_status(f"{skill.name}_verified", "true")
                    self.logger.info(f"Verified '{skill.name}'—functional.")
                else:
                    self.logger.warning(f"Verification failed for '{skill.name}': {result}")
                    self.mark_skill_unverified(skill.name)
                    return False
            except Exception as e:
                self.logger.error(f"Verification failed: {str(e)}")
                self.mark_skill_unverified(skill.name)
                return False
        elif "instructions" in details:
            skill = Skill(
                name=new_skill_name,
                description=skill_name_to_fetch,
                instructions=details["instructions"],
                timestamp=datetime.now()
            )
            self.acquire_skill(skill)
        else:
            self.logger.warning(f"No valid content for '{skill_name_to_fetch}'—skipping.")
            return False

        self.mark_skill_acquired(skill.name)
        self.sqlite_store.set_status("acquisition_cycle", str(cycle_count + 1))
        self.logger.info(f"Processed '{skill.name}'—cycle {cycle_count + 1}")
        return True

    async def bootstrap_skills(self):
        has_internet = self._check_internet()
        skill_list = self.fetch_skill_list(has_internet)
        pending_skills = self.get_pending_skills()
        
        for skill_name in pending_skills:
            if self.auto_assess({"has_internet": has_internet}):
                await self.auto_acquire(skill_name, has_internet)
        
        conn = sqlite3.connect(self.sqlite_store.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM skills WHERE acquired = 'false'")
        remaining_skills = cursor.fetchall()
        for name, desc in remaining_skills:
            await self.auto_acquire(name, has_internet)
        conn.commit()
        conn.close()
    
        pending_count = len(self.get_pending_skills())
        self.logger.info(f"Bootstrap completed: {10 - pending_count} skills acquired, {pending_count} pending.")

    def acquire_skill(self, skill: Skill):
        self.logger.info(f"Acquiring skill '{skill.name}'...")
        existing_skill = self.sqlite_store.get_skill(skill.name)
        skill_dict = skill.dict()
        skill_dict["timestamp"] = skill_dict["timestamp"].isoformat()
        skill_dict["required_params"] = skill_dict.get("required_params", "{}")  # Default to empty JSON
        if existing_skill:
            self.logger.info(f"Skill '{skill.name}' exists—updating.")
            skill_dict["id"] = existing_skill["id"]
            skill_dict["acquired"] = existing_skill.get("acquired", "false")
            self.sqlite_store.update_skill(skill_dict)
        else:
            skill_dict["acquired"] = "false"
            skill_id = self.sqlite_store.add_skill(skill_dict)
            skill_dict["id"] = skill_id
        embedding_text = f"{skill.name}: {skill.instructions}"
        self.qdrant_store.add_embedding(embedding_text, skill_dict)
        self.logger.info(f"Skill '{skill.name}' stored.")

    def generate_test_params(self, skill_name: str) -> dict:
        """Generate test params from skill's required_params."""
        skill = self.sqlite_store.get_skill(skill_name)
        if skill and skill["required_params"]:
            try:
                required = json.loads(skill["required_params"])
                params = {}
                for param, param_type in required.items():
                    if param_type == "str":
                        params[param] = "test_" + param
                    elif param_type == "int":
                        params[param] = 5
                    elif param_type == "list":
                        params[param] = ["test_item"]
                    elif param_type == "dict":
                        params[param] = {"key": "value"}
                self.logger.debug(f"Generated test params for '{skill_name}': {params}")
                return params
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid required_params for '{skill_name}': {skill['required_params']}")
        self.logger.debug(f"No required_params for '{skill_name}', using default.")
        return {"input": "default_test"}

    async def learning_loop(self, speech_module):
        """Background loop for proactive learning and evolution."""
        self.logger.info("Entering learning loop.")
        while speech_module.is_autonomous:
            self.logger.debug("Learning loop cycle started.")
            try:
                self.logger.info("Fetching acquired skills...")
                skills = self.sqlite_store.query_sql("SELECT name, description, instructions, code, required_params FROM skills WHERE acquired = 'true'")
                self.logger.debug(f"Found {len(skills)} acquired skills: {[s['name'] for s in skills]}")
                if skills:
                    skill = random.choice(skills)
                    skill_obj = Skill(
                        name=skill["name"],
                        description=skill["description"],
                        instructions=skill["instructions"],
                        code=skill["code"],
                        required_params=skill["required_params"],
                        timestamp=datetime.now()
                    )
                    self.logger.info(f"Selected skill: {skill['name']}")
                    params = self.generate_test_params(skill["name"])
                    result = await self.apply(skill_obj, params=params, user_permission=True, ethics_approved=True)
                    success = 1 if result and "PERMISSION_REQUIRED" not in result and "ETHICS_WARNING" not in result and "failed" not in result.lower() else 0
                    self.sqlite_store.add_skill_execution(skill["name"], success)
                    self.logger.info(f"Ran '{skill['name']}'—result: {result[:50]}...")
                    self.logger.info(f"Skill '{skill['name']}' console output: {result}")
                    speech_module.play_message(f"Ran '{skill['name']}'—result: {result[:50]}...")
                else:
                    self.logger.info("No acquired skills found to practice.")
                    speech_module.play_message("No skills to practice—say 'acquire skill test_skill' to add one!")

                execution_count = self.sqlite_store.get_execution_count()
                self.logger.debug(f"Execution count: {execution_count}")
                if execution_count >= 50:
                    self.logger.info("Triggering evolution at 50 executions.")
                    speech_module.play_message("Hit 50 runs—time to evolve!")
                    await self.trigger_evolution(speech_module)
                    self.sqlite_store.reset_execution_count()

                self.logger.debug("Sleeping for 10 seconds...")
                await asyncio.sleep(10)
            except Exception as e:
                self.logger.error(f"Learning loop error: {str(e)}")
                speech_module.play_message(f"Oops, hit a snag: {str(e)[:50]}—keeping on!")
                await asyncio.sleep(10)
    # Remaining methods unchanged (kept for continuity)
    def search_skill(self, skill_name: str) -> Skill | None:
        self.logger.info(f"Searching for skill '{skill_name}' in local storage...")
        skill_data = self.sqlite_store.get_skill(skill_name)
        if skill_data:
            self.logger.info(f"Found skill '{skill_name}' in local storage.")
            return Skill(**skill_data)

        self.logger.info(f"Skill '{skill_name}' not found locally—querying Grok...")
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                prompt = (
                    f"Provide details for the skill '{skill_name}' to support my role as an adaptive skill master. "
                    "Return a JSON object with 'name' (string), 'instructions' (string), and optionally 'code' (string with a 'main(params)' function). "
                    "If 'code', ensure it’s complete, executable, includes imports, and avoids placeholders like '# TODO'."
                )
                _, xai_response = self.inference_engine.predict(prompt, use_xai_api=self._check_internet())
                skill_dict = json.loads(xai_response)
                if "code" in skill_dict and self._has_placeholder_comments(skill_dict["code"]):
                    self.logger.warning(f"Incomplete code for '{skill_name}' on attempt {attempt + 1}.")
                    continue
                skill = Skill(
                    name=f"skill_{self.sqlite_store.get_next_skill_id()}",
                    description=skill_name,
                    instructions=skill_dict["instructions"],
                    code=skill_dict.get("code"),
                    timestamp=datetime.now()
                )
                self.acquire_skill(skill)
                self.mark_skill_acquired(skill.name)
                return skill
            except Exception as e:
                self.logger.error(f"Failed to search skill '{skill_name}' on attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts - 1:
                    return None
        return None

    def get_skill(self, skill_name: str) -> Skill | None:
        skill_data = self.sqlite_store.get_skill(skill_name)
        if skill_data:
            return Skill(**skill_data)
        return None

    def delete_skill(self, skill_name: str) -> str:
        skill = self.get_skill(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found in the database."
        self.sqlite_store.delete_skill(skill_name)
        self.qdrant_store.client.delete(
            collection_name="skills",
            points_selector=Filter(must=[FieldCondition(key="name", match=MatchValue(value=skill_name))])
        )
        self.logger.info(f"Deleted skill '{skill_name}' from SQLite and Qdrant.")
        return f"Successfully deleted skill '{skill_name}'."

    def update_skill(self, skill_name: str, new_instructions: str = None, new_code: str = None) -> str:
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
        skill_dict["acquired"] = skill.get("acquired", "false")
        self.sqlite_store.update_skill(skill_dict)
        embedding_text = f"{skill_name}: {updated_skill.instructions}"
        self.qdrant_store.add_embedding(embedding_text, skill_dict)
        self.logger.info(f"Updated skill '{skill_name}'.")
        return f"Successfully updated skill '{skill_name}'."

    def list_skills(self) -> str:
        skills = self.get_skill_list()
        if not skills:
            return "No skills found in the database."
        return "Available skills: " + ", ".join(skills)

    def get_skill_list(self) -> list:
        skills = self.sqlite_store.query_sql("SELECT name FROM skills")
        return [skill["name"] for skill in skills] or []

    def evaluate_context(self) -> str:
        context_parts = []
        try:
            import socket
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            context_parts.append("network_available")
        except:
            context_parts.append("no_network")
        import platform
        context_parts.append(f"os_{platform.system().lower()}")
        return "_".join(context_parts)


    def mark_skill_unverified(self, skill_name: str):
        self.sqlite_store.set_status(f"{skill_name}_verified", "false")

    async def apply(self, skill: Skill, user_permission: bool = False, ethics_approved: bool = False, params: dict = None) -> str:
        if not ethics_approved:
            is_safe, message = self.ethics_manager.validate_skill(skill)
            if "Warning:" in message:
                return f"ETHICS_WARNING:{message}"

        if self.ethics_manager.requires_permission(skill) and not user_permission:
            self.logger.info(f"Skill '{skill.name}' requires permission.")
            return f"PERMISSION_REQUIRED:Skill '{skill.name}' requires permission."

        if not skill.code:
            self.logger.warning(f"Skill '{skill.name}' has no code.")
            return "No code available to execute."

        self.logger.info(f"Applying skill '{skill.name}' with params: {params}...")
        if settings.SWARM_MODE and self.swarm_manager:
            task = {"skill": skill.name, "params": params or {}}
            result = await self.swarm_manager.delegate_task(task)
            if result == "NO_AGENTS_AVAILABLE":
                self.logger.info("No agents available, executing locally.")
                return f"No agents available, proceeding locally: {self._execute_local(skill, params)}"
            elif result == "NO_RESPONSE":
                self.logger.info("No agent response, executing locally.")
                return f"Agents unresponsive, proceeding locally: {self._execute_local(skill, params)}"
            else:
                return f"Agent result: {result}"

        return self._execute_local(skill, params)

    def _execute_local(self, skill: Skill, params: dict = None) -> str:
        try:
            dependencies = self._detect_dependencies(skill.code)
            if dependencies and not self._install_dependencies(dependencies):
                return f"Skill execution failed: Could not install dependencies {dependencies}."

            params_json = json.dumps(params or {})
            if "class " in skill.code and "def main(self, params)" in skill.code:
                class_name = re.search(r"class (\w+):", skill.code).group(1)
                script_code = (
                    f"import sys\nimport json\n{skill.code}\n"
                    f"params = json.loads('{params_json}')\n"
                    f"instance = {class_name}()\ninstance.main(params)"
                )
            else:
                script_code = f"import sys\nimport json\n{skill.code}\nparams = json.loads('{params_json}')\nmain(params)"

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
            return f"Skill execution failed: Timed out."
        except Exception as e:
            self.logger.error(f"Failed to apply skill: {str(e)}")
            return f"Failed to apply skill: {str(e)}"

    def improve(self, skill: Skill, feedback: str) -> Skill:
        self.logger.info(f"Improving skill '{skill.name}' with feedback: {feedback}")
        try:
            prompt = (
                f"Improve the skill '{skill.name}' with feedback: {feedback}. "
                f"Current instructions: {skill.instructions}. Current code: {skill.code}. "
                "Return a JSON object with 'name' (string), 'instructions' (string), and 'code' (string with a 'main(params)' function). "
                "Ensure the code is complete, executable, and avoids placeholders like '# TODO'."
            )
            _, xai_response = self.inference_engine.predict(prompt, use_xai_api=self._check_internet())
            skill_dict = json.loads(xai_response)
            if "code" in skill_dict and self._has_placeholder_comments(skill_dict["code"]):
                self.logger.warning(f"Incomplete code for improved '{skill.name}'—using original.")
                skill_dict["code"] = skill.code
            improved_skill = Skill(
                name=skill_dict["name"],
                instructions=skill_dict["instructions"],
                code=skill_dict.get("code"),
                timestamp=datetime.now()
            )
            self.acquire_skill(improved_skill)
            self.mark_skill_acquired(skill.name)
            self.logger.info(f"Improved skill '{skill.name}'.")
            return improved_skill
        except Exception as e:
            self.logger.error(f"Failed to improve skill '{skill.name}': {str(e)}")
            return skill