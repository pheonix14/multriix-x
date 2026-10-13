/*
 * MULTRIIX X — Native C++ CLI Verification Suite
 * Project: MULTRIIX X | Author: Pheonix14 / ZeroX
 * Language: C++17
 */

#include <iostream>
#include <string>
#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <sstream>

namespace fs = std::filesystem;

int test_binary_in_path() {
    std::cout << "[TEST C++] Checking mx binary installation in PATH..." << std::endl;
    int res = std::system("command -v mx > /dev/null 2>&1");
    assert(res == 0 && "mx binary must be available in PATH");
    std::cout << "  ✓ mx binary is located and executable in PATH" << std::endl;
    return 0;
}

int test_mx_version_execution() {
    std::cout << "[TEST C++] Testing 'mx version' output..." << std::endl;
    int res = std::system("mx version > /dev/null 2>&1");
    assert(res == 0 && "'mx version' must return exit code 0");
    std::cout << "  ✓ 'mx version' executed successfully" << std::endl;
    return 0;
}

int test_mx_status_execution() {
    std::cout << "[TEST C++] Testing 'mx status' telemetry..." << std::endl;
    int res = std::system("mx status > /dev/null 2>&1");
    assert(res == 0 && "'mx status' must return exit code 0");
    std::cout << "  ✓ 'mx status' telemetry reported successfully" << std::endl;
    return 0;
}

int test_savegame_workflow() {
    std::cout << "[TEST C++] Testing full savegame workflow via C++ binary..." << std::endl;
    // Save
    int save_res = std::system("mx save test_cpp_slot -d 'C++ Test Save' > /dev/null 2>&1");
    assert(save_res == 0 && "'mx save' failed");

    // List
    int list_res = std::system("mx saves > /dev/null 2>&1");
    assert(list_res == 0 && "'mx saves' failed");

    // Load
    int load_res = std::system("mx load test_cpp_slot > /dev/null 2>&1");
    assert(load_res == 0 && "'mx load' failed");

    std::cout << "  ✓ Savegame cycle (save -> list -> load) verified via C++ CLI" << std::endl;
    return 0;
}

int main() {
    std::cout << "\n============================================================" << std::endl;
    std::cout << "  MULTRIIX X — C++ CLI VERIFICATION SUITE" << std::endl;
    std::cout << "============================================================" << std::endl;

    test_binary_in_path();
    test_mx_version_execution();
    test_mx_status_execution();
    test_savegame_workflow();

    std::cout << "============================================================" << std::endl;
    std::cout << "  ALL C++ TESTS PASSED (4/4) — ZERO CRASHES" << std::endl;
    std::cout << "============================================================\n" << std::endl;
    return 0;
}
