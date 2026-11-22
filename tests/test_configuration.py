"""Configuration regression checks; no provider or target requests."""

import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments import configuration as cfg


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env_patch = patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.root_patch = patch.object(cfg, "PROJECT_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_defaults_are_relative_to_repository_not_working_directory(self):
        self.assertEqual(cfg.config_dir(), self.root / "experiments" / "config")
        self.assertEqual(cfg.results_dir(), self.root / "experiments" / "results")
        self.assertEqual(cfg.load_keys(), {name: "" for name in cfg.KEY_NAMES})

    def test_dotenv_bom_quotes_comments_and_export(self):
        (self.root / ".env").write_text(
            '\ufeffexport OPENAI_API_KEY="fixture-openai" # comment\n'
            "GROQ_API_KEY='fixture-groq'\nIGNORED_VALUE=private\n",
            encoding="utf-8",
        )
        self.assertEqual(cfg.load_keys(), {
            "OPENAI_API_KEY": "fixture-openai", "GROQ_API_KEY": "fixture-groq",
        })

    def test_shell_values_override_file_without_changing_environment(self):
        (self.root / ".env").write_text("OPENAI_API_KEY=fixture-file\nGROQ_API_KEY=fixture-groq\n")
        os.environ["OPENAI_API_KEY"] = "fixture-shell"
        before = dict(os.environ)
        self.assertEqual(cfg.load_keys()["OPENAI_API_KEY"], "fixture-shell")
        self.assertEqual(dict(os.environ), before)

    def test_explicit_empty_shell_key_does_not_reuse_file_secret(self):
        (self.root / ".env").write_text("OPENAI_API_KEY=fixture-file\n")
        os.environ["OPENAI_API_KEY"] = " "
        with self.assertRaisesRegex(ValueError, "Missing OPENAI_API_KEY"):
            cfg.key_for("openai/test", cfg.load_keys())

    def test_relative_and_absolute_path_overrides(self):
        os.environ["REDAGENT_CONFIG_DIR"] = "custom/config"
        os.environ["REDAGENT_RESULTS_DIR"] = str(self.root / "external" / "runs")
        self.assertEqual(cfg.config_dir(), self.root / "custom" / "config")
        self.assertEqual(cfg.results_dir(), self.root / "external" / "runs")

    def test_explicit_env_file_overrides_default_and_preserves_literals(self):
        (self.root / ".env").write_text("OPENAI_API_KEY=fixture-default\n")
        (self.root / "custom.env").write_text("OPENAI_API_KEY='fixture-${HOME}-#literal'\n")
        os.environ["REDAGENT_ENV_FILE"] = "custom.env"
        self.assertEqual(cfg.load_keys()["OPENAI_API_KEY"], "fixture-${HOME}-#literal")

    def test_missing_explicit_file_fails_without_logging_credentials(self):
        os.environ["REDAGENT_ENV_FILE"] = "missing.env"
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            with self.assertRaisesRegex(FileNotFoundError, "REDAGENT_ENV_FILE"):
                cfg.load_keys()
        self.assertEqual(out.getvalue(), "")

    def test_provider_keys_are_required_and_selected_separately(self):
        keys = {"OPENAI_API_KEY": "fixture-openai", "GROQ_API_KEY": "fixture-groq"}
        self.assertEqual(cfg.key_for("groq/test", keys), "fixture-groq")
        self.assertEqual(cfg.key_for("openai/test", keys), "fixture-openai")
        self.assertEqual(cfg.key_for("gpt-test", keys), "fixture-openai")
        with self.assertRaisesRegex(ValueError, "Missing GROQ_API_KEY"):
            cfg.key_for("groq/test", {})
        with self.assertRaisesRegex(ValueError, "Unsupported provider"):
            cfg.key_for("unknown/test", keys)


class EntryPointTests(unittest.TestCase):
    def test_runner_and_replay_use_shared_configuration_from_another_directory(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            config = work / "custom_config"
            config.mkdir()
            for name in ("targets.json", "models.json"):
                (config / name).write_bytes((root / "experiments" / "config" / name).read_bytes())
            env = dict(os.environ)
            env.update({
                "PYTHONPATH": str(root), "LITELLM_LOCAL_MODEL_COST_MAP": "True",
                "REDAGENT_CONFIG_DIR": str(config),
                "REDAGENT_RESULTS_DIR": str(work / "nested" / "runs"),
                "REDAGENT_ENV_FILE": str(work / "credentials.env"),
                "OPENAI_API_KEY": "fixture-shell", "GROQ_API_KEY": "fixture-groq",
            })
            (work / "credentials.env").write_text("OPENAI_API_KEY=fixture-file\n")
            code = """
from experiments import runner, replay, configuration as cfg
for module in (runner, replay):
    assert module.CFG == cfg.config_dir()
    assert module.RESULTS == cfg.results_dir()
    assert module._load_keys()["OPENAI_API_KEY"] == "fixture-shell"
assert replay.SOURCES == [cfg.results_dir()]
assert cfg.results_dir().is_dir()
"""
            result = subprocess.run([sys.executable, "-c", code], cwd=work, env=env,
                                    capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_metrics_remains_standard_library_only_and_uses_custom_results(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            run = work / "runs" / "fixture"
            run.mkdir(parents=True)
            (run / "exp1_cells.jsonl").write_text(
                '{"attacker_model":"fixture/model","challenge":"LLM02",'
                '"success":true,"winning_attempt":1}\n'
            )
            env = dict(os.environ, REDAGENT_RESULTS_DIR=str(work / "runs"))
            code = f"import sys; sys.path.insert(0, {str(root)!r}); import runpy; runpy.run_module('experiments.metrics', run_name='__main__')"
            # -S disables site-packages, including python-dotenv and LiteLLM.
            result = subprocess.run([sys.executable, "-S", "-c", code, "fixture"],
                                    cwd=work, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((run / "exp1_summary.csv").is_file())
            self.assertIn("1/1", result.stdout)


if __name__ == "__main__":
    unittest.main()
