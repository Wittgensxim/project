import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class EnvironmentTests(unittest.TestCase):
    def test_parse_opt_version_extracts_version_target_and_cpu(self):
        from ecpor.environment import parse_opt_version

        text = """LLVM (http://llvm.org/):
  LLVM version 23.0.0git
  Optimized build.
  Default target: x86_64-w64-windows-gnu
  Host CPU: znver5
"""

        info = parse_opt_version(text)

        self.assertEqual(info["llvm_version"], "23.0.0git")
        self.assertEqual(info["target_triple"], "x86_64-w64-windows-gnu")
        self.assertEqual(info["host_cpu"], "znver5")

    def test_parse_clang_version_extracts_commit(self):
        from ecpor.environment import parse_clang_version

        text = """clang version 23.0.0git (https://github.com/llvm/llvm-project.git aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2)
Target: x86_64-w64-windows-gnu
Thread model: posix
InstalledDir: E:/llvm/build/bin
"""

        info = parse_clang_version(text)

        self.assertEqual(info["clang_version"], "23.0.0git")
        self.assertEqual(
            info["clang_commit"], "aac212f0bc9acbc40a8a2e9638f4b7496c25d0b2"
        )

    def test_compute_env_id_is_stable_and_sensitive_to_version(self):
        from ecpor.environment import LLVMEnvironment, compute_env_id

        base = LLVMEnvironment(
            opt_path="E:/llvm/build/bin/opt.exe",
            clang_path="E:/llvm/build/bin/clang.exe",
            llvm_size_path="E:/llvm/build/bin/llvm-size.exe",
            llvm_config_path="E:/llvm/build/bin/llvm-config.exe",
            llvm_version="23.0.0git",
            clang_version="23.0.0git",
            clang_commit="abc",
            target_triple="x86_64-w64-windows-gnu",
            host_cpu="znver5",
        )
        changed = LLVMEnvironment(
            opt_path="E:/llvm/build/bin/opt.exe",
            clang_path="E:/llvm/build/bin/clang.exe",
            llvm_size_path="E:/llvm/build/bin/llvm-size.exe",
            llvm_config_path="E:/llvm/build/bin/llvm-config.exe",
            llvm_version="23.0.1git",
            clang_version="23.0.0git",
            clang_commit="abc",
            target_triple="x86_64-w64-windows-gnu",
            host_cpu="znver5",
        )

        self.assertEqual(compute_env_id(base), compute_env_id(base))
        self.assertNotEqual(compute_env_id(base), compute_env_id(changed))

    def test_file_sha256_hashes_file_content(self):
        from ecpor.environment import file_sha256

        path = Path(__file__).resolve().parent / "sample-tool.bin"
        path.write_bytes(b"tool bytes")
        try:
            self.assertEqual(
                file_sha256(path),
                "b0335dc5c19f374fb20d56c5e3764727a1dc64df38c0a2f4239d35a6ef4a3e82",
            )
        finally:
            path.unlink()

    def test_compute_env_id_is_sensitive_to_tool_hashes(self):
        from ecpor.environment import LLVMEnvironment, compute_env_id

        base = LLVMEnvironment(
            opt_path="E:/llvm/build/bin/opt.exe",
            clang_path="E:/llvm/build/bin/clang.exe",
            llvm_size_path="E:/llvm/build/bin/llvm-size.exe",
            llvm_config_path="E:/llvm/build/bin/llvm-config.exe",
            llvm_version="23.0.0git",
            clang_version="23.0.0git",
            clang_commit="abc",
            target_triple="x86_64-w64-windows-gnu",
            host_cpu="znver5",
            opt_sha256="opt-a",
            clang_sha256="clang-a",
            llvm_size_sha256="size-a",
        )
        changed = LLVMEnvironment(
            opt_path="E:/llvm/build/bin/opt.exe",
            clang_path="E:/llvm/build/bin/clang.exe",
            llvm_size_path="E:/llvm/build/bin/llvm-size.exe",
            llvm_config_path="E:/llvm/build/bin/llvm-config.exe",
            llvm_version="23.0.0git",
            clang_version="23.0.0git",
            clang_commit="abc",
            target_triple="x86_64-w64-windows-gnu",
            host_cpu="znver5",
            opt_sha256="opt-b",
            clang_sha256="clang-a",
            llvm_size_sha256="size-a",
        )

        self.assertNotEqual(compute_env_id(base), compute_env_id(changed))


if __name__ == "__main__":
    unittest.main()
