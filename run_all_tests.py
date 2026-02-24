import os
import subprocess
import sys
import time

def run_all_tests():
    test_dir = "tests"
    if not os.path.exists(test_dir):
        print(f"Error: {test_dir} directory not found.")
        return

    test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
    test_files.sort()

    passed = []
    failed = []

    print("=" * 60)
    print(f"PyEngine Master Test Runner - Found {len(test_files)} test suites")
    print("=" * 60)

    start_time = time.time()

    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        print(f"Running {test_file}...", end="", flush=True)
        
        try:
            # Set PYTHONPATH so that 'src' is discoverable
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(".") + os.pathsep + env.get("PYTHONPATH", "")
            
            # Run test as a separate process to avoid state contamination
            result = subprocess.run(
                [sys.executable, test_path],
                capture_output=True,
                text=True,
                env=env,
                timeout=60 # 1 minute timeout per test suite
            )
            
            if result.returncode == 0:
                print(" [PASS]")
                passed.append(test_file)
            else:
                print(" [FAIL]")
                failed.append((test_file, result.stderr or result.stdout))
        except subprocess.TimeoutExpired:
            print(" [TIMEOUT]")
            failed.append((test_file, "Test timed out after 60 seconds"))
        except Exception as e:
            print(f" [ERROR: {str(e)}]")
            failed.append((test_file, str(e)))

    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(test_files)}")
    print(f"Passed:      {len(passed)}")
    print(f"Failed:      {len(failed)}")
    print(f"Duration:    {duration:.2f}s")
    print("=" * 60)

    if failed:
        print("\n" + "!" * 60)
        print("FAILURE DETAILS:")
        print("!" * 60)
        for test_file, error in failed:
            print(f"\n[FAILED] {test_file}")
            print("-" * 20)
            print(error)
            print("-" * 20)
        
        print("\nFailed Tests:")
        for test_file, _ in failed:
            print(f"  - {test_file}")
            
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
