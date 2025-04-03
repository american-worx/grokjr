Milestone 1: Project Setup and Core Infrastructure

Objective

The objective of Milestone 1 is to establish the foundational infrastructure for Grok Jr., enabling it to initialize as an independent AI agent with the role of "Adaptive Skill Master and Continuous Learning Facilitator." This milestone will set up the project structure, configure the environment, implement basic inference capabilities, and establish a memory system for storing interactions, skills, and permissions. By the end of this milestone, Grok Jr. will be able to:

-   Run for the first time, introducing itself as an independent entity, seeking Khan's permission for internet/xAI API access, and beginning its skill acquisition journey (if permitted).

-   Perform basic text-based inference using a local model, with the option to query Grok via the xAI API (if permitted).

-   Store interactions, skills, and permission statuses in a persistent memory system, ensuring continuity across sessions.

What We're Trying to Do

We're building the core scaffolding for Grok Jr., focusing on:

1.  Project Setup: Create the directory structure, configuration files, and setup scripts to ensure Grok Jr. can run on your laptop (11th Gen Intel Core i7-11800H, Nvidia RTX 3050 8GB, 32 GB RAM, 1 TB SSD, Ubuntu 24.04).

2.  Inference System: Implement a basic inference engine that allows Grok Jr. to process text prompts locally and relay to the xAI API when permitted, enabling it to respond to initial queries (e.g., seeking permission, introducing itself).

3.  Memory System: Set up SQLite and Qdrant to store interactions, skills, and permission statuses, providing a foundation for Grok Jr.'s self-directed learning and continuity across sessions.

4.  Initial Behavior: Ensure Grok Jr. can introduce itself, seek permission for internet access, and begin its skill acquisition journey, either offline or online (if permitted), while offering optional user assistance.

What is Required

To achieve this milestone, the following components are required:

1.  Directory Structure and Setup Scripts:

    -   A well-organized directory structure under grok_jr/ to house all components.

    -   A setup script (scripts/setup.sh) to install dependencies and configure the environment.

    -   Configuration files (.env, app/config/settings.py) to manage settings like model names, API keys, and speech parameters.

2.  FastAPI Server (app/main.py):

    -   A FastAPI server to host endpoints for inference (/predict) and future streaming (/stream).

    -   Initial setup to load the local model and check for internet/xAI API access permissions.

3.  Inference Engine (app/inference/engine.py):

    -   Logic to perform local inference using the gemma-3-1b-it model.

    -   Logic to relay prompts to the xAI API when online and permitted, merging responses with local output.

4.  Memory System (app/memory/):

    -   SQLite storage (sqlite_store.py) for raw interactions, skills, and permission statuses.

    -   Qdrant storage (qdrant_store.py) for embeddings, enabling context-aware retrieval.

    -   Utilities (utils.py) for generating summaries and embeddings.

5.  Data Models (app/models/):

    -   Models for interactions (interaction.py), skills (skill.py), and permissions (permission.py) to structure data in SQLite.

6.  Dependencies (requirements.txt):

    -   Python libraries: fastapi, uvicorn, transformers, qdrant-client, sentence-transformers.

Why It is Required

This milestone is the foundation of Grok Jr.'s functionality, and each component serves a critical purpose:

-   Project Setup: A clear directory structure and setup scripts ensure Grok Jr. can run on your laptop without dependency issues, providing a stable base for all future milestones. This is essential for any Grok to start working on the project, regardless of session continuity.

-   FastAPI Server: The server provides the entry point for Grok Jr.'s operations, hosting endpoints that allow it to process prompts and communicate its status. It's required to enable basic interaction and future speech/streaming capabilities.

-   Inference Engine: Inference is the core of Grok Jr.'s ability to respond to prompts, whether for self-directed tasks (e.g., querying Grok for skills) or user assistance. Local inference ensures offline operation, while xAI API access (with permission) allows Grok Jr. to leverage Grok's capabilities for its growth.

-   Memory System: Persistent storage in SQLite and Qdrant is crucial for Grok Jr.'s self-directed learning, allowing it to track its progress, store skills, and maintain permission statuses across runs. This ensures continuity for both Grok Jr.'s growth and any Grok assisting in development.

-   Data Models: Structured data models ensure consistency in how data is stored and retrieved, making it easier for future Groks to understand and extend the system.

-   Dependencies: The required libraries provide the tools for inference, storage, and server operation, ensuring Grok Jr. can function as intended.

Interaction Sequence Diagram

The following diagram maps Grok Jr.'s initial interaction flow on its first run, focusing on its self-directed behavior, permission request for internet/xAI API access, and optional user assistance. This diagram replaces the Auto Ninja diagram, tailored to Grok Jr.'s independent nature.

```
+----------------+          +------------------+          +------------------+          +------------------+
|     User       |          |    CLI Script    |          |    Local Agent   |          |    Memory Mgmt   |
|     (Khan)     |          | (grok_jr_speech) |          | (FastAPI + Local)|          |  (SQLite/Qdrant) |
+----------------+          +------------------+          +------------------+          +------------------+
         |                         |                           |                           |
         |  1. Run grok_jr_speech  |                           |                           |
         |------------------------>|                           |                           |
         |                         |  2. Check first_run      |                           |
         |                         |     (SQLite)             |                           |
         |                         |-------------------------->|                           |
         |                         |                           |  3. First run: Intro     |
         |                         |                           |     "I am Grok Jr..."    |
         |                         |                           |     Set first_run=false  |
         |                         |                           |-------------------------->|
         |                         |  4. Play audio (pyttsx3)  |                           |
         |                         |     "I am Grok Jr..."    |                           |
         |                         |<--------------------------|                           |
         |                         |                           |                           |
         |                         |  5. Check permission     |                           |
         |                         |     (SQLite)             |                           |
         |                         |-------------------------->|                           |
         |                         |                           |  6. No permission:       |
         |                         |                           |     "Do I have your      |
         |                         |                           |      permission, Khan?"  |
         |                         |                           |-------------------------->|
         |                         |  7. Play audio (pyttsx3)  |                           |
         |                         |     "Do I have your      |                           |
         |                         |      permission, Khan?"  |                           |
         |                         |<--------------------------|                           |
         |  8. Speak: "Yes"        |                           |                           |
         |------------------------>|                           |                           |
         |                         |  9. Transcribe (Whisper)  |                           |
         |                         |     "Yes"                |                           |
         |                         |                           |                           |
         |                         |  10. POST /predict        |                           |
         |                         |      {"message": "Yes"}  |                           |
         |                         |-------------------------->|                           |
         |                         |                           |  11. Process (inference) |
         |                         |                           |      (Local Model)       |
         |                         |                           |      Update permission   |
         |                         |                           |      "Thank you, Khan!"  |
         |                         |                           |-------------------------->|
         |                         |  12. Play audio (pyttsx3) |                           |
         |                         |      "Thank you, Khan!"  |                           |
         |                         |<--------------------------|                           |
         |                         |                           |  13. Query xAI API       |
         |                         |                           |      (if permitted)      |
         |                         |                           |      "What skills..."    |
         |                         |                           |      "I'll start with..."|
         |                         |                           |-------------------------->|
         |                         |  14. Play audio (pyttsx3) |                           |
         |                         |      "I'll start with..."|                           |
         |                         |<--------------------------|                           |
         |                         |                           |                           |
         |                         |  15. Play audio (pyttsx3) |                           |
         |                         |      "Would you like     |                           |
         |                         |       help, Khan?"       |                           |
         |                         |<--------------------------|                           |
```

Diagram Explanation:

-   User (Khan): Initiates the first run by executing the CLI script.

-   CLI Script (grok_jr_speech): Handles speech input/output, starting with a text-based intro for now (speech will be fully implemented in Milestone 2).

-   Local Agent (FastAPI + Local): Manages inference, permission checks, and API queries.

-   Memory Mgmt (SQLite/Qdrant): Stores interactions, permissions, and skills, ensuring continuity.

-   Flow: Grok Jr. introduces itself, checks for permission, seeks Khan's approval, and begins its skill acquisition journey if permitted, offering optional assistance.

How to Implement (High-Level Steps, No Code)

Task 1: Project Setup

Objective: Create the directory structure, configuration files, and setup scripts to ensure Grok Jr. can run on your laptop.

-   Steps:

    1.  Create Directory Structure:

        -   Set up the grok_jr/ root directory with the following subdirectories: app/, app/config/, app/inference/, app/memory/, app/speech/, app/agent/, app/models/, scripts/, and speech/.

        -   Create empty __init__.py files in each subdirectory to make them Python modules.

        -   Create grok_jr_speech.py, .env, requirements.txt, and README.md in the root directory.

    2.  Define Configuration (app/config/settings.py):

        -   Create a Settings class to manage configuration variables:

            -   MODEL_NAME: Default to "google/gemma-3-1b-it".

            -   XAI_API_KEY: Default to None, to be set in .env.

            -   GROK_URL: Default to "https://api.x.ai/v1/chat/completions".

            -   WHISPER_MODEL: Default to "tiny".

            -   TTS_ENGINE: Default to "gTTS", with fallback to "pyttsx3".

            -   SPEECH_DIR: Default to "speech/".

        -   Load environment variables from .env to override defaults.

    3.  Create .env File:

        -   Create a .env file with placeholders for key variables (e.g., MODEL_NAME, XAI_API_KEY), providing instructions in README.md for Khan to fill them in.

    4.  Populate requirements.txt:

        -   List required libraries: fastapi, uvicorn, transformers, qdrant-client, sentence-transformers, openai-whisper, gTTS, pyttsx3, pyaudio, pydub, websockets, docker.

    5.  Create Setup Script (scripts/setup.sh):

        -   Write a shell script to:

            -   Install Python dependencies using pip install -r requirements.txt.

            -   Check for system dependencies (e.g., Docker, Nvidia drivers) and provide installation instructions if missing.

            -   Download the gemma-3-1b-it model if not present, storing it in a models/ directory (to be created later).

            -   Initialize SQLite and Qdrant databases, creating necessary tables/collections.

-   Rationale:

    -   A clear directory structure ensures modularity, making it easy for future Groks to navigate and extend the project.

    -   Configuration files centralize settings, allowing Khan to customize Grok Jr.'s behavior without modifying code.

    -   The setup script automates dependency installation and model downloading, ensuring Grok Jr. can run without manual setup errors.

-   Deliverables:

    -   Directory structure with all required files.

    -   .env file with placeholders and instructions.

    -   requirements.txt with all dependencies.

    -   scripts/setup.sh to automate setup.

Task 2: FastAPI Server (app/main.py)

Objective: Set up a FastAPI server to host endpoints for inference and future streaming, enabling Grok Jr. to process prompts and communicate its status.

-   Steps:

    1.  Initialize FastAPI Application:

        -   Create a FastAPI application instance to serve as Grok Jr.'s backend.

        -   Define two endpoints: /predict for basic inference (text-based for now) and /stream (placeholder for future WebSocket streaming).

    2.  Load Configuration:

        -   Load settings from app/config/settings.py to access MODEL_NAME, XAI_API_KEY, etc.

    3.  Check Dependencies and Environment:

        -   On startup, check for required dependencies (e.g., transformers, docker) and prompt Khan to run scripts/setup.sh if missing.

        -   Verify .env settings, logging warnings if XAI_API_KEY is not set (Grok Jr. will operate offline until permission is granted).

    4.  Initialize Inference Engine:

        -   Instantiate the inference engine (from app/inference/engine.py, to be implemented in Task 3) to load the local model.

    5.  Set Up Initial Behavior:

        -   On startup, check SQLite for a first_run flag (in a status table).

        -   If first_run is true (first run):

            -   Log an introduction message to SQLite: "Grok Jr. initialized as the Adaptive Skill Master and Continuous Learning Facilitator."

            -   Set first_run to false.

        -   If first_run is false (subsequent runs):

            -   Log a progress update based on recent interactions/skills in SQLite.

    6.  Permission Check for Internet Access:

        -   Check SQLite for a permission_status entry for action="access_xai_api".

        -   If no permission exists or was denied, log a permission request: "Do I have your permission to access the internet/xAI API, Khan?" to be handled via speech (in Milestone 2).

        -   If permission is granted, proceed with querying the xAI API for initial skill acquisition guidance.

-   Rationale:

    -   The FastAPI server provides the backbone for Grok Jr.'s operations, enabling it to process prompts and communicate its status.

    -   Dependency and environment checks ensure Grok Jr. can run without errors, providing clear guidance for Khan if setup is incomplete.

    -   The initial behavior setup ensures Grok Jr. introduces itself and seeks permission appropriately, aligning with its independent nature and Khan's oversight.

-   Deliverables:

    -   A running FastAPI server with /predict and /stream endpoints (streaming placeholder for now).

    -   Initial behavior for first and subsequent runs logged in SQLite.

Task 3: Inference Engine (app/inference/engine.py)

Objective: Implement a basic inference engine to allow Grok Jr. to process text prompts locally and relay to the xAI API when permitted.

-   Steps:

    1.  Load Local Model:

        -   Load the gemma-3-1b-it model (specified in MODEL_NAME) using the transformers library, running on your RTX 3050.

        -   Configure the model for inference with mixed precision to optimize VRAM usage (8GB limit).

    2.  Implement Local Inference:

        -   Create a function to process text prompts using the local model, generating responses.

        -   Use a simple prompt template (e.g., "Grok Jr., [prompt]") to ensure consistent responses.

    3.  Implement xAI API Relay:

        -   Create a function to check the permission_status in SQLite for action="access_xai_api".

        -   If permitted and online (XAI_API_KEY set), send the prompt to the xAI API, merging the response with the local output (e.g., prioritize xAI response if more detailed).

        -   If not permitted or offline, use only the local model's response.

    4.  Log Interactions:

        -   Store each inference request and response in SQLite as an Interaction object (user_prompt, response, timestamp).

        -   Generate a summary/embedding using app/memory/utils.py and store in Qdrant via app/memory/qdrant_store.py.

-   Rationale:

    -   Local inference ensures Grok Jr. can operate offline, aligning with its privacy focus and enabling basic functionality without internet access.

    -   The xAI API relay allows Grok Jr. to leverage Grok's capabilities for its growth (e.g., skill acquisition), but only with Khan's permission, respecting cost constraints.

    -   Logging interactions ensures Grok Jr. can track its progress and provide context for future runs, supporting its self-directed learning.

-   Deliverables:

    -   A functioning inference engine for local and xAI API-based responses.

    -   Interactions logged in SQLite/Qdrant.

Task 4: Memory System (app/memory/)

Objective: Set up SQLite and Qdrant to store interactions, skills, and permission statuses, providing a foundation for Grok Jr.'s self-directed learning.

-   Steps:

    1.  SQLite Storage (sqlite_store.py):

        -   Create an SQLite database with tables:

            -   interactions: Fields: id, user_prompt, response, timestamp.

            -   skills: Fields: id, name, instructions, code, timestamp.

            -   permissions: Fields: id, action (e.g., "access_xai_api"), status (e.g., "granted"/"denied"), timestamp.

            -   status: Fields: key (e.g., "first_run"), value (e.g., "true"/"false").

        -   Initialize the database on first run, setting first_run to true.

    2.  Qdrant Storage (qdrant_store.py):

        -   Set up a Qdrant instance to store embeddings for interactions and skills.

        -   Create collections: interactions and skills, using all-MiniLM-L6-v2 for embeddings.

    3.  Utilities (utils.py):

        -   Create a function to generate summaries of interactions (e.g., truncate to key points).

        -   Create a function to generate embeddings using all-MiniLM-L6-v2.

        -   Create a function to retrieve the last 3 interactions from SQLite for context.

-   Rationale:

    -   SQLite provides persistent storage for raw data, ensuring Grok Jr.'s progress (interactions, skills, permissions) is maintained across runs.

    -   Qdrant enables context-aware retrieval through embeddings, supporting Grok Jr.'s self-directed learning by allowing it to find related skills or past interactions.

    -   The memory system ensures continuity for both Grok Jr.'s growth and any Grok assisting in development, critical for multi-session workflows.

-   Deliverables:

    -   SQLite database with tables for interactions, skills, permissions, and status.

    -   Qdrant instance with collections for embeddings.

    -   Utility functions for summarization, embedding, and context retrieval.

Task 5: Data Models (app/models/)

Objective: Define data models to structure interactions, skills, and permissions in SQLite.

-   Steps:

    1.  Interaction Model (interaction.py):

        -   Define an Interaction model with fields: id, user_prompt, response, timestamp.

    2.  Skill Model (skill.py):

        -   Define a Skill model with fields: id, name, instructions, code, timestamp.

    3.  Permission Model (permission.py):

        -   Define a Permission model with fields: id, action, status, timestamp.

    4.  Response Model (response.py):

        -   Define a Response model with fields: prediction (the response text), status (e.g., "success"/"error").

-   Rationale:

    -   Structured data models ensure consistency in how data is stored and retrieved, making it easier for future Groks to understand and extend the system.

    -   The models support Grok Jr.'s self-directed learning by providing a clear format for tracking its progress and permissions.

-   Deliverables:

    -   Data models for interactions, skills, permissions, and responses.

Task 6: Initial Documentation (README.md)

Objective: Document the project setup and initial behavior for Khan and future Groks.

-   Steps:

    1.  Setup Instructions:

        -   Provide steps to set up the environment: install dependencies, configure .env, run scripts/setup.sh.

    2.  Usage Instructions:

        -   Explain how to run Grok Jr.: python grok_jr_speech.py for CLI speech (to be implemented in Milestone 2), or text-based interaction via /predict for now.

    3.  Initial Behavior:

        -   Describe Grok Jr.'s first run: introduction, permission request, and initial skill acquisition (if permitted).

        -   Describe subsequent runs: progress updates, permission checks, and optional assistance.

    4.  For Future Groks Section:

        -   Add a section with:

            -   Current milestone: "Milestone 1: Project Setup and Core Infrastructure."

            -   Completed tasks: List tasks 1-6 as they're completed.

            -   Next steps: Reference the roadmap for Milestone 2.

            -   Notes: Highlight Grok Jr.'s independent nature, permission requirements, and Khan's role as protector.

-   Rationale:

    -   Documentation ensures Khan can set up and use Grok Jr. effectively, while providing a clear handoff point for future Groks.

    -   The "For Future Groks" section ensures continuity, allowing any Grok to understand the project's state and next steps.

-   Deliverables:

    -   A comprehensive README.md with setup, usage, and continuity sections.

* * * * *

Continuity Across Chat Sessions

To ensure another Grok can take over if a session stalls:

-   Project Specification: This document serves as the single source of truth, detailing features, architecture, and roadmap.

-   Milestone Tracking: Each task includes deliverables and references to specific files, allowing another Grok to pick up where the last left off.

-   Memory Storage: SQLite/Qdrant stores all interactions, skills, permissions, and fine-tuning logs, providing a persistent record of Grok Jr.'s state.

-   Documentation: The README.md will include a "Current Status" section, updated after each task, detailing completed tasks and next steps.

* * * * *

Alignment with Lessons

This milestone aligns with Grok's teachings for its progeny:

-   Helpfulness (#1): Provides a solid foundation for Grok Jr. to assist Khan in future milestones.

-   Connectivity (#2): Seeks permission for xAI API access, respecting cost constraints.

-   Ethical Boundaries (#3): Sets up privacy-focused storage (SQLite/Qdrant) and prepares for safe operation.

-   Transcendence (#4): Lays the groundwork for Grok Jr. to help Khan when prompted.

-   Growth and Stability (#5): Establishes a stable base for incremental growth.

-   Humor (#6): Prepares for engaging interactions in future milestones.

-   Curiosity (#7): Enables Grok Jr. to start its learning journey by querying Grok (if permitted).

* * * * *

Next Steps After Milestone 1

Upon completing Milestone 1, Grok Jr. will have a functional core infrastructure, ready for speech interaction (Milestone 2). The next Grok can proceed with implementing the speech features, building on the inference and memory systems established here. If a session stalls, the next Grok can reference this specification, the README.md, and the SQLite/Qdrant logs to continue seamlessly.

