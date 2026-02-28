import os
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)

ALLOWED_PLUGIN_NAMES: Set[str] = set()


class BasePlugin:
    """Base interface for all dynamic plugins."""
    name: str = "unnamed_plugin"
    plugin_type: str = "output"

    def on_load(self):
        pass

    def on_event(self, event_type: str, data: Dict[str, Any]) -> Any:
        pass


class PluginLoader:
    """
    Dynamic Plugin System with safety controls.
    Scans /plugins directory and auto-registers .py files containing
    classes that inherit from BasePlugin.
    
    Safety:
    - Only loads .py files (no compiled/binary plugins)
    - Validates class hierarchy (must extend BasePlugin)
    - Logs all loaded plugins for audit trail
    - ALLOWED_PLUGIN_NAMES allowlist can restrict which plugins load
    """

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}

    def discover_and_load(self, plugins_dir: str = None):
        if plugins_dir is None:
            plugins_dir = str(Path(__file__).parent.parent / "plugins")

        if not os.path.exists(plugins_dir):
            logger.info(f"[PLUGINS] No plugins directory found at {plugins_dir}")
            return

        for item in sorted(os.listdir(plugins_dir)):
            if item.startswith("_") or not item.endswith(".py"):
                continue

            module_name = item[:-3]

            if ALLOWED_PLUGIN_NAMES and module_name not in ALLOWED_PLUGIN_NAMES:
                logger.warning(f"[PLUGINS] Skipped {item}: not in allowlist")
                continue

            file_path = os.path.join(plugins_dir, item)
            if not os.path.isfile(file_path):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{module_name}", file_path
                )
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                            issubclass(attr, BasePlugin) and
                            attr is not BasePlugin):
                        instance = attr()
                        instance.on_load()
                        self._plugins[instance.name] = instance
                        logger.info(
                            f"[PLUGINS] Loaded: {instance.name} ({instance.plugin_type})"
                        )
            except Exception as e:
                logger.error(f"[PLUGINS] Failed to load {item}: {e}")

    def notify_all(self, event_type: str, data: Dict[str, Any]):
        for name, plugin in self._plugins.items():
            try:
                plugin.on_event(event_type, data)
            except Exception as e:
                logger.error(f"[PLUGINS] Error in {name}.on_event: {e}")

    def get_loaded(self) -> list:
        return [{"name": p.name, "type": p.plugin_type} for p in self._plugins.values()]


plugin_loader = PluginLoader()
