from importlib.metadata import version

from butler_core import PluginDefinition

import wilfred_home_assistant


def test_version() -> None:
    assert version("butler-home-assistant") == "0.2.0.dev0"
    assert wilfred_home_assistant.__version__ == "0.2.0.dev0"


def test_core_plugin_contract_available() -> None:
    assert PluginDefinition.__name__ == "PluginDefinition"
