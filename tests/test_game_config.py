"""Majesty Gold HD's game.toml renders the values the kit's hooks expect."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "kit"

# The zero-filled section padding after .rsrc in the pinned "MajestyHD - Old.exe":
# mapped, never referenced by the game. Every unidentified hook and global
# lives in its last 512 bytes.
SENTINEL_LOW, SENTINEL_HIGH = 0x00725E00, 0x00726000


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, KIT / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


game_config = load_module("game_config")
gen_game_config = load_module("gen_game_config")


class MajestyConfigTests(unittest.TestCase):
    def setUp(self):
        self.cfg = game_config.load(ROOT)
        self.header = gen_game_config.render_header(self.cfg)

    def test_identity(self):
        self.assertEqual(self.cfg["game"]["id"], "majesty")
        self.assertEqual(self.cfg["game"]["executable"], "MajestyHD - Old.exe")
        self.assertEqual(self.cfg["game"]["sha256"],
                         "654365fd1bdefa6d7f2349d162869f255388fadcb1bb8db9f7db2f3468dd5542")
        self.assertEqual(self.cfg["game"]["entry_point"], 0x0064D96D)
        self.assertEqual(self.cfg["game"]["image_base"], 0x00400000)
        self.assertIn('#define RECOMP_APP_NAME "MajestyRecomp"', self.header)
        self.assertIn('#define RECOMP_EXECUTABLE "MajestyHD - Old.exe"', self.header)
        self.assertIn('#define RECOMP_GUEST_ROOT "C:\\\\GOG Games\\\\Majesty Gold HD"', self.header)
        self.assertEqual(self.cfg["developer_exe_path"], (ROOT / "original/gog/MajestyHD - Old.exe").resolve())
        self.assertEqual(self.cfg["listings_path"],
                         (ROOT / "analysis/decompiled/MajestyHD - Old.exe").resolve())

    def test_every_kit_macro_is_rendered(self):
        for macro in ("RECOMP_HOOK_FRAME_CLOCK_BEGIN", "RECOMP_HOOK_FRAME_CLOCK_WAIT",
                      "RECOMP_HOOK_FRAME_CLOCK_WAIT_CLAMP", "RECOMP_HOOK_FRAME_CLOCK_CLAMP_DEADLINE",
                      "RECOMP_HOOK_FRAME_CLOCK_WAIT_DEADLINE", "RECOMP_HOOK_CURSOR_SURFACE_PTRS_COUNT 2",
                      "RECOMP_HOOK_MOUSE_VTABLE", "RECOMP_HOOK_MOUSE_DEVICE_PTR", "RECOMP_HOOK_MOUSE_DEVICE_RIGHT",
                      "RECOMP_HOOK_CAMERA", "RECOMP_GLOBAL_SIMULATION_TURN_ADDR", "RECOMP_GLOBAL_COMMAND_FRAME_ADDR",
                      "RECOMP_GLOBAL_ENTITY_BASE_ADDR", "RECOMP_GLOBAL_ENTITY_BASE_STRIDE",
                      "RECOMP_GLOBAL_ENTITY_BASE_COUNT"):
            self.assertIn("#define " + macro, self.header)

    def test_unidentified_addresses_stay_in_the_sentinel_padding(self):
        """Until a hook is found, it must point where the game never looks."""
        addresses = [self.cfg["translate"]["animation_counter"]]
        for value in self.cfg["hooks"].values():
            addresses += value if isinstance(value, list) else [value]
        addresses += [entry["addr"] for entry in self.cfg["globals"].values()]
        for address in addresses:
            self.assertTrue(SENTINEL_LOW <= address < SENTINEL_HIGH, hex(address))
        self.assertEqual(len(addresses), len(set(addresses)), "sentinels must not alias one another")
        self.assertEqual(self.cfg["translate"]["volatile_reads"], [])

    def test_bundle_exclusions_and_setup(self):
        for pattern in ("__redist", "SDK", "tmp", "*.dll", "MajestyHD.exe"):
            self.assertIn(pattern, self.cfg["bundle"]["exclude"])
        # The pinned executable's own name must survive the exclusion list.
        stage = load_module("stage_game_files")
        self.assertFalse(stage.excluded(Path("MajestyHD - Old.exe"), self.cfg["bundle"]["exclude"]))
        self.assertTrue(stage.excluded(Path("MajestyHD.exe"), self.cfg["bundle"]["exclude"]))
        self.assertTrue(stage.excluded(Path("Galaxy.dll"), self.cfg["bundle"]["exclude"]))
        self.assertFalse(stage.excluded(Path("Data/maindata.cam"), self.cfg["bundle"]["exclude"]))
        self.assertEqual(self.cfg["setup"]["required_dirs"], ["Data", "DataMX", "Quests", "QuestsMX", "Music"])
        self.assertNotIn("annotations_url", self.cfg["setup"])


if __name__ == "__main__":
    unittest.main()
