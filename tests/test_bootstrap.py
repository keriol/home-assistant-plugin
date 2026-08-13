from importlib.metadata import version

from wilfred.plugins import PluginDefinition

import wilfred_home_assistant


def test_version() -> None:
    assert version("wilfred-home-assistant") == "0.1.0.dev0"
    assert wilfred_home_assistant.__version__ == "0.1.0.dev0"


def test_wilfred_plugin_contract_available() -> None:
    assert PluginDefinition.__name__ == "PluginDefinition"
