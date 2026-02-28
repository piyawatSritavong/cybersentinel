import os
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent.parent / "skills"


class SkillEngine:
    """
    Dynamic Skill Engine: The AI can write its own tools.
    When a threat is detected that current tools can't handle, the Agent can:
    1. Research the threat pattern
    2. Code a new .py Skill in /app/skills/
    3. Hot-reload the skill without restarting
    """

    def __init__(self):
        self._skills: Dict[str, dict] = {}
        os.makedirs(SKILLS_DIR, exist_ok=True)
        init_file = SKILLS_DIR / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
        self._discover_existing()

    def _discover_existing(self):
        for f in SKILLS_DIR.glob("*.py"):
            if f.name.startswith("_"):
                continue
            name = f.stem
            self._skills[name] = {
                "name": name,
                "description": f"Loaded from {f.name}",
                "file": str(f),
                "status": "loaded"
            }
            logger.info(f"[SKILL-ENGINE] Discovered existing skill: {name}")

    def list_skills(self) -> list:
        return list(self._skills.values())

    def generate_skill(self, name: str, description: str) -> dict:
        """
        Use the AI to generate a new skill based on a description,
        then save it to disk and hot-load it.
        """
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in name.lower())

        prompt = f"""You are an expert Python security tool developer.
Generate a Python function that implements the following security skill:

Name: {safe_name}
Description: {description}

Requirements:
1. Write a single Python function named `execute_{safe_name}` that takes relevant parameters
2. The function should return a dict with 'status', 'result', and 'details' keys
3. Include proper error handling and logging
4. Import only from standard library or commonly available packages
5. Add a docstring explaining what the function does
6. Keep it focused and atomic

Output ONLY the Python code, no markdown formatting or explanation.
"""

        try:
            llm = ChatGroq(
                api_key=settings.groq_api_key,
                model_name=settings.analyst_model,
                temperature=0.2,
            )
            response = llm.invoke(prompt)

            code = response.content.strip()
            if code.startswith("```"):
                lines = code.split("\n")
                code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

            skill_path = SKILLS_DIR / f"{safe_name}.py"
            skill_path.write_text(code)

            self._skills[safe_name] = {
                "name": safe_name,
                "description": description,
                "file": str(skill_path),
                "status": "generated"
            }

            self._hot_load(safe_name, skill_path)

            logger.info(f"[SKILL-ENGINE] Generated and loaded new skill: {safe_name}")
            return {
                "name": safe_name,
                "status": "generated",
                "file": str(skill_path),
                "description": description
            }

        except Exception as e:
            logger.error(f"[SKILL-ENGINE] Failed to generate skill {name}: {e}")
            return {"name": name, "status": "error", "error": str(e)}

    def _hot_load(self, name: str, path: Path):
        """Hot-load a skill module without restarting."""
        try:
            spec = importlib.util.spec_from_file_location(f"skills.{name}", str(path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._skills[name]["status"] = "loaded"
                logger.info(f"[SKILL-ENGINE] Hot-loaded: {name}")
        except Exception as e:
            self._skills[name]["status"] = f"load_error: {e}"
            logger.error(f"[SKILL-ENGINE] Hot-load failed for {name}: {e}")


skill_engine = SkillEngine()
