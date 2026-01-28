import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomHook(BuildHookInterface):
  def initialize(self, version, build_data):
    build_data["pure_python"] = False

    platform = "win_amd64" if sys.platform == "win32" else "linux_x86_64"
    build_data["tag"] = f"py3-none-{platform}"
