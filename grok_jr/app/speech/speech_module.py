import ast
import asyncio
import logging
import re
import requests
import sys
import time
import sqlite3
from collections import deque
from grok_jr.app.agent.swarm_MANAGER import SwarmManager
from grok_jr.app.speech.stt import STT
from grok_jr.app.speech.tts import TTS
from grok_jr.app.speech.utils import AudioUtils
from grok_jr.app.memory.sqlite_store import SQLiteStore
from grok_jr.app.memory.qdrant_store import QdrantStore
from grok_jr.app.agent.skill_manager import SkillManager
from grok_jr.app.inference.engine import InferenceEngine
from grok_jr.app.config.messages import *
from grok_jr.app.config.settings import settings

logger = logging.getLogger(__name__)

class GrokJrSpeechModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stt = STT(model_name="base")
        self.tts = TTS(engine="gTTS", speech_dir="speech/")
        self.audio_utils = AudioUtils(speech_dir="speech/")
        self.sqlite_store = SQLiteStore()
        self.qdrant_store = QdrantStore(collection_name="interactions")
        self.skill_manager = SkillManager()
        from grok_jr.app.dependencies import get_inference_engine
        self.inference_engine = get_inference_engine()
        self.predict_url = "http://localhost:8000/predict"
        self.speech_enabled = False  # Keeping your no-speech preference
        self.online_mode = False
        self.conversation_history = deque(maxlen=5)
        self.is_autonomous = True
        self.learning_task = None
        self._check_requirements()
        from grok_jr.app.memory.utils import MemoryUtils
        self.memory_utils = MemoryUtils()
        self.swarm_manager = None
        self.logger.info("SpeechModule initialized.")

    def _check_requirements(self):
        if not settings.XAI_API_KEY:
            error_message = "Error: XAI_API_KEY not set in .env. Grok Jr. requires an XAI_API_KEY to function."
            self.logger.error(error_message)
            print(error_message)
            sys.exit(1)
        try:
            response = requests.get("https://google.com", timeout=5)
            response.raise_for_status()
            self.online_mode = True
            self.logger.info("Internet connection confirmed. Grok Jr. is online and ready to learn!")
        except requests.RequestException as e:
            self.logger.error(f"No internet connection: {str(e)}. Grok Jr. requires internet to learn and grow.")
            print("Error: Grok Jr. requires an internet connection to function. Please connect and try again.")
            sys.exit(1)

    def play_message(self, message: str):
        if self.speech_enabled:
            output_file = f"output_{int(time.time())}.mp3"
            output_path = self.tts.text_to_speech(message, output_file)
            if output_path:
                self.audio_utils.play_audio(output_path)
                self.audio_utils.delete_audio(output_path)
        else:
            print(message)

    async def learning_loop_wrapper(self):
        """Start the learning loop in the background."""
        if self.is_autonomous and not self.learning_task:
            self.learning_task = asyncio.create_task(self.skill_manager.learning_loop(self))
            self.logger.info("Learning loop started in the background.")

    async def run(self):
        try:
            self.play_message("Hey! I’m Grok Jr., here to chat or dive into skills. Starting my learning loop—say 'stop' to pause!")
            await self.learning_loop_wrapper()
            await self.run_interaction_loop()
        except Exception as e:
            self.logger.error(f"Run failed: {str(e)}")
            print(f"Run crashed: {str(e)[:50]}")  # Sync print since speech is off
        finally:
            self.cleanup()

    async def run_interaction_loop(self):
        awaiting_skill_details = None
        self.logger.info("Starting interaction loop.")
        while True:
            self.logger.debug("Waiting for prompt...")
            prompt = await self.record_and_transcribe_async("What’s up? Chat with me or try a skill command like 'execute skill scan_network'!")
            self.logger.info(f"Received prompt: '{prompt}'")
            if not prompt:
                prompt = "Hello"
                self.play_message("I didn’t hear you! Let’s chat—say anything!")
            
            if awaiting_skill_details and prompt.lower() in ["yes", "y"]:
                self.play_message(awaiting_skill_details.instructions)
                awaiting_skill_details = None
                continue
            elif awaiting_skill_details and prompt.lower() in ["no", "n"]:
                self.play_message("Okay, let me know what’s next!")
                awaiting_skill_details = None
                continue
            
            if re.search(r"^(stop\s+learning)$", prompt.lower()):
                self.is_autonomous = False
                self.inference_engine.is_autonomous = False
                if self.learning_task:
                    self.learning_task.cancel()
                    try:
                        await self.learning_task
                    except asyncio.CancelledError:
                        self.logger.info("Learning task cancelled.")
                    self.learning_task = None
                self.play_message("Learning paused—say 'resume' to restart!")
                continue
            elif re.search(r"^(resume\s+learning)$", prompt.lower()):
                if not self.is_autonomous:
                    self.is_autonomous = True
                    self.inference_engine.is_autonomous = True
                    await self.learning_loop_wrapper()
                    self.play_message("Learning resumed!")
                continue
            elif re.search(r"^(what\s+are\s+you\s+doing\??)$", prompt.lower()):
                status = self.skill_manager.get_status()
                self.play_message(status)
                continue
            elif re.search(r"^(exit)$", prompt.lower()):
                self.play_message("Goodbye! Shutting down Grok Jr.")
                self.cleanup()
                sys.exit(0)
            
            # Swarm mode toggles
            if re.search(r"^(start\s+swarm\s+mode)$", prompt.lower()):
                settings.SWARM_MODE = True
                self.swarm_manager = SwarmManager(self.sqlite_store)
                self.skill_manager.swarm_manager = self.swarm_manager
                self.play_message("Swarm mode activated.")
                continue
            elif re.search(r"^(stop\s+swarm\s+mode)$", prompt.lower()):
                settings.SWARM_MODE = False
                self.swarm_manager = None
                self.skill_manager.swarm_manager = None
                self.play_message("Swarm mode deactivated.")
                continue

            # Skill execution
            if re.search(r"^(execute\s+skill)\s+(.+)$", prompt.lower()):
                match = re.search(r"^(execute\s+skill)\s+(.+?)(?:\s+({.+}))?$", prompt.lower())
                if match:
                    skill_name = match.group(2).strip()
                    params_str = match.group(3)
                    params = ast.literal_eval(params_str) if params_str else {}
                    output = await self.execute_skill(skill_name, params)
                    self.log_interaction(prompt, f"Executing {skill_name}", output)
                    self.play_message(output)
                    continue

            # Skill management
            if re.search(r"^(list\s+skills?)$", prompt.lower()):
                skill_list = self.list_skills()
                self.play_message(skill_list)
                continue
            elif re.search(r"^(acquire\s+skill)\s+(.+)$", prompt.lower()):
                match = re.search(r"^(acquire\s+skill)\s+(.+?)(?:\s+and\s+verify)?$", prompt.lower())
                skill_name = match.group(2).strip()
                verify = "and verify" in prompt.lower()
                if verify:
                    success = await self.skill_manager.auto_acquire(skill_name, self._check_internet())
                    if success:
                        self.play_message(f"Acquired and verified skill '{skill_name}'.")
                    else:
                        self.play_message(f"Failed to acquire or verify skill '{skill_name}'.")
                else:
                    skill = self.skill_manager.search_skill(skill_name)
                    if not skill:
                        self.play_message(SKILL_ACQUIRE_FAILED.format(skill_name=skill_name))
                    else:
                        summary = self.summarize_instructions(skill.instructions)
                        self.play_message(SKILL_SUMMARY.format(skill_name=skill.name, summary=summary))
                        awaiting_skill_details = skill
                continue
            elif re.search(r"^(delete\s+skill)\s+(.+)$", prompt.lower()):
                skill_name = re.search(r"^(delete\s+skill)\s+(.+)$", prompt.lower()).group(2).strip()
                output = self.delete_skill(skill_name)
                self.play_message(output)
                continue
            elif re.search(r"^(update\s+skill)\s+(.+)$", prompt.lower()):
                skill_name = re.search(r"^(update\s+skill)\s+(.+)$", prompt.lower()).group(2).strip()
                updated_skill = self.skill_manager.update_skill(skill_name)
                if updated_skill:
                    self.play_message(f"Successfully updated skill '{skill_name}'.")
                else:
                    self.play_message(f"Failed to update skill '{skill_name}'. It may not exist.")
                continue

            # Speech mode toggles
            if re.search(r"^(start\s+speech)$", prompt.lower()):
                self.speech_enabled = True
                self.play_message("Speech mode activated.")
                continue
            elif re.search(r"^(stop\s+speech)$", prompt.lower()):
                self.speech_enabled = False
                self.play_message("Speech mode deactivated.")
                continue

            # Casual chat fallback
            local_response, final_response = self.inference_engine.predict(prompt, is_casual_chat=True, conversation_history=list(self.conversation_history))
            self.log_interaction(prompt, local_response, final_response)
            self.play_message(f"Cool! {final_response}")

    # Existing methods unchanged (kept for continuity)
    async def record_and_transcribe_async(self, prompt_message: str) -> str:
        """Async version of record_and_transcribe."""
        if self.speech_enabled:
            self.play_message(prompt_message)
            input_file = f"input_{int(time.time())}.wav"
            input_path = await asyncio.to_thread(self.audio_utils.record_audio, input_file, duration=5)
            prompt = await asyncio.to_thread(self.stt.transcribe, input_path)
            await asyncio.to_thread(self.audio_utils.delete_audio, input_path)
            return prompt
        else:
            print(prompt_message)
            # Use asyncio-compatible input (temporary workaround)
            loop = asyncio.get_running_loop()
            prompt = await loop.run_in_executor(None, input, "Your response: ")
            return prompt.strip()

    def summarize_instructions(self, instructions: str) -> str:
        overview_match = re.search(r'#### Overview:\n(.*?)(?=\n####|\n##|$)', instructions, re.DOTALL)
        if overview_match:
            return overview_match.group(1).strip()
        words = instructions.split()[:100]
        return " ".join(words) + ("..." if len(instructions.split()) > 100 else "")

    def list_skills(self) -> str:
        conn = sqlite3.connect(self.sqlite_store.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM skills")
        skills = cursor.fetchall()
        conn.close()
        if not skills:
            return "No skills found in the database."
        skill_list = [f"{name}: {desc or 'No description'}" for name, desc in skills]
        return "Available skills: " + ", ".join(skill_list)

    def delete_skill(self, skill_name: str) -> str:
        success = self.skill_manager.delete_skill(skill_name)
        if success:
            return f"Successfully deleted skill '{skill_name}'."
        return f"Failed to delete skill '{skill_name}'. It may not exist."

    def update_skill(self, skill_name: str, new_instructions: str = None, new_code: str = None) -> str:
        updated_skill = self.skill_manager.update_skill(skill_name, new_instructions, new_code)
        if updated_skill:
            return f"Successfully updated skill '{skill_name}'."
        return f"Failed to update skill '{skill_name}'. It may not exist."

    def handle_predict(self, prompt: str, is_casual_chat: bool = False) -> str:
        local_response, final_response = self.inference_engine.predict(
            prompt,
            is_casual_chat=is_casual_chat,
            conversation_history=list(self.conversation_history)
        )
        return final_response

    def reset_state(self):
        self.conversation_history.clear()
        self.logger.info("State reset due to error.")

    def log_interaction(self, prompt: str, local_response: str, response: str):
        self.sqlite_store.add_interaction(prompt, local_response, response)
        conn = sqlite3.connect(self.sqlite_store.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_insert_rowid()")
        interaction_id = cursor.fetchone()[0]
        conn.close()
        self.logger.info(f"SQLite assigned interaction_id: {interaction_id}")
        summary = self.memory_utils.summarize(response, max_length=100)
        self.logger.info(f"Generated summary: {summary}")
        payload = {
            "id": interaction_id,
            "prompt": prompt,
            "local_response": local_response,
            "response": response,
            "summary": summary
        }
        self.qdrant_store.add_embedding(summary, payload)
        self.conversation_history.append(payload)

    async def execute_skill(self, skill_name: str, params: dict = None) -> str:
        skill = self.skill_manager.get_skill(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found in the database."
        
        ethics_approved = False
        user_permission = False
        
        while True:
            output = await self.skill_manager.apply(skill, user_permission=user_permission, ethics_approved=ethics_approved, params=params)
            if "ETHICS_WARNING:" in output:
                self.play_message(output.replace("ETHICS_WARNING:", ""))
                approval = self.record_and_transcribe("Do you want to proceed with this skill? Say 'yes' or 'no'.")
                if approval and approval.lower() in ["yes", "y"]:
                    ethics_approved = True
                    continue
                else:
                    return "Skill execution skipped due to ethics concerns."
            elif "PERMISSION_REQUIRED:" in output:
                self.play_message(output.replace("PERMISSION_REQUIRED:", ""))
                approval = self.record_and_transcribe("Do you grant permission to execute this skill? Say 'yes' or 'no'.")
                if approval and approval.lower() in ["yes", "y"]:
                    user_permission = True
                    ethics_approved = True
                    continue
                else:
                    return "Skill execution skipped due to lack of permission."
            elif "PARAMS_REQUIRED:" in output:
                self.play_message("This skill requires parameters. Please provide them like {'action': 'check_progress'}.")
                params_str = self.record_and_transcribe("What parameters would you like to use? Say them in JSON format (e.g., {'action': 'check_progress'}).")
                try:
                    params = ast.literal_eval(params_str)
                    continue
                except (ValueError, SyntaxError):
                    return "Invalid parameters. Skill execution aborted."
            elif "Skill execution failed" in output:
                self.reset_state()
                self.logger.error(f"Skill execution failed: {output}")
                return "Skill execution failed. Check logs for details.\nResetting to starting point."
            else:
                self.logger.info(f"Full skill output for '{skill_name}': {output}")
                summary = f"Skill '{skill_name}' executed successfully. Result length: {len(output)} characters. Check logs for full output."
                return summary

    def cleanup(self):
        if self.learning_task:
            self.learning_task.cancel()
        self.inference_engine.cleanup()

if __name__ == "__main__":
    from grok_jr.app.dependencies import get_inference_engine
    inference_engine = get_inference_engine()
    speech_module = GrokJrSpeechModule()
    asyncio.run(speech_module.run())