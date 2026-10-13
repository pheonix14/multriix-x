/*
 * MULTRIIX X — High-Performance Native CLI (mx)
 * Project: MULTRIIX X | Author: Pheonix14 / ZeroX
 * Language: C++17
 *
 * Allows instant execution from any terminal:
 *   $ mx                  -> Run Multriix AI Manager directly
 *   $ mx run [--legacy]   -> Run NeuralDesk or Legacy TRON interface
 *   $ mx status           -> System diagnostics & port health
 *   $ mx save <name>      -> Save current memory to named cartridge
 *   $ mx load <name>      -> Load / restore a savegame cartridge
 *   $ mx saves / mx list  -> List all savegame cartridges with checksum status
 *   $ mx info <file>      -> Verify SHA-256 integrity and inspect cartridge
 *   $ mx export <s <path> -> Export savegame cartridge for travel
 *   $ mx import <path>    -> Import travel cartridge into local inventory
 *   $ mx qs / mx ql       -> QuickSave / QuickLoad
 *   $ mx test             -> Run full Multriix test suite in real time
 */

#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#include <sstream>
#include <fstream>
#include <filesystem>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <signal.h>

namespace fs = std::filesystem;

// ANSI Terminal Colors
namespace Color {
    const std::string RESET   = "\033[0m";
    const std::string BOLD    = "\033[1m";
    const std::string DIM     = "\033[2m";
    const std::string RED     = "\033[31m";
    const std::string GREEN   = "\033[32m";
    const std::string YELLOW  = "\033[33m";
    const std::string BLUE    = "\033[34m";
    const std::string MAGENTA = "\033[35m";
    const std::string CYAN    = "\033[36m";
    const std::string WHITE   = "\033[37m";
}

void printBanner() {
    std::cout << Color::CYAN << Color::BOLD
              << "  ███╗   ███╗██╗   ██╗██╗  ████████╗██████╗ ██╗██╗██╗  ██╗   ██╗  ██╗\n"
              << "  ████╗ ████║██║   ██║██║  ╚══██╔══╝██╔══██╗██║██║╚██╗██╔╝   ╚██╗██╔╝\n"
              << "  ██╔████╔██║██║   ██║██║     ██║   ██████╔╝██║██║ ╚███╔╝     ╚███╔╝ \n"
              << "  ██║╚██╔╝██║██║   ██║██║     ██║   ██╔══██╗██║██║ ██╔██╗     ██╔██╗ \n"
              << "  ██║ ╚═╝ ██║╚██████╔╝███████╗██║   ██║  ██║██║██║██╔╝ ██╗██╗██╔╝ ██╗\n"
              << "  ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝\n"
              << Color::RESET;
    std::cout << Color::MAGENTA << "  [ NATIVE CLI ENGINE | ZEROX / PHEONIX14 | HIGH-THROUGHPUT RUNTIME ]\n"
              << Color::RESET << std::endl;
}

void printHelp() {
    printBanner();
    std::cout << Color::BOLD << "USAGE:" << Color::RESET << "\n"
              << "  " << Color::GREEN << "mx" << Color::RESET << "                    Launch Multriix directly in current terminal\n"
              << "  " << Color::GREEN << "mx run [--legacy]" << Color::RESET << "     Run NeuralDesk UI or legacy TRON server\n"
              << "  " << Color::GREEN << "mx status" << Color::RESET << "             Inspect engine status, ports, and active memory\n"
              << "  " << Color::GREEN << "mx save <name>" << Color::RESET << "       Save current memory snapshot as a savegame\n"
              << "  " << Color::GREEN << "mx load <name>" << Color::RESET << "       Load a savegame slot or .mxsave cartridge\n"
              << "  " << Color::GREEN << "mx load <name> --merge" << Color::RESET << " Merge savegame into active memory without duplicates\n"
              << "  " << Color::GREEN << "mx qs / mx ql" << Color::RESET << "        QuickSave or QuickLoad instant checkpoint\n"
              << "  " << Color::GREEN << "mx saves / mx list" << Color::RESET << "   List all memory cartridges and save slots\n"
              << "  " << Color::GREEN << "mx info <file>" << Color::RESET << "        Verify SHA-256 checksum and inspect cartridge\n"
              << "  " << Color::GREEN << "mx export <slot> <path>" << Color::RESET << " Export portable cartridge to take anywhere\n"
              << "  " << Color::GREEN << "mx import <path>" << Color::RESET << "       Import travel cartridge into local inventory\n"
              << "  " << Color::GREEN << "mx test" << Color::RESET << "               Run master unit test suite in real time\n"
              << "  " << Color::GREEN << "mx help / --help" << Color::RESET << "     Show this documentation\n"
              << "\n"
              << Color::DIM << "Tip: You can travel with .mxsave files across any device or OS!" << Color::RESET << "\n\n";
}

// Locate Multriix installation directory
std::string findMultriixRoot() {
    // 1. Environment variable
    const char* envPath = std::getenv("MULTRIXX_HOME");
    if (envPath && fs::exists(envPath)) {
        return envPath;
    }

    // 2. Standard Termux install directory
    const std::string termuxPath = "/data/data/com.termux/files/home/multriix-x";
    if (fs::exists(termuxPath)) {
        return termuxPath;
    }

    // 3. User home directory
    const char* home = std::getenv("HOME");
    if (home) {
        std::string homePath = std::string(home) + "/multriix-x";
        if (fs::exists(homePath)) return homePath;
    }

    // 4. Current working directory or parent
    if (fs::exists("multriix_x/core")) return fs::current_path().string();
    if (fs::exists("../multriix_x/core")) return fs::canonical("..").string();

    return termuxPath;
}

int executeBridge(const std::string& multriixRoot, const std::vector<std::string>& bridgeArgs) {
    std::string bridgeScript = multriixRoot + "/multriix_x/cli/mx_bridge.py";
    if (!fs::exists(bridgeScript)) {
        std::cerr << Color::RED << "[FAIL] Could not locate mx_bridge.py at: " << bridgeScript << Color::RESET << std::endl;
        return 1;
    }

    std::ostringstream cmd;
    cmd << "python3 \"" << bridgeScript << "\"";
    for (const auto& arg : bridgeArgs) {
        cmd << " \"" << arg << "\"";
    }

    return std::system(cmd.str().c_str());
}

int launchMultriix(const std::string& multriixRoot, bool legacy) {
    printBanner();
    std::cout << Color::GREEN << "[OK] Launching MULTRIIX X from: " << Color::BOLD << multriixRoot << Color::RESET << "\n";

    std::string mainPy = multriixRoot + "/main.py";
    if (!fs::exists(mainPy)) {
        std::cerr << Color::RED << "[FAIL] Master entrypoint missing: " << mainPy << Color::RESET << std::endl;
        return 1;
    }

    std::ostringstream cmd;
    cmd << "python3 \"" << mainPy << "\"";
    if (legacy) {
        cmd << " --legacy";
    }

    return std::system(cmd.str().c_str());
}

int main(int argc, char* argv[]) {
    std::vector<std::string> args;
    for (int i = 1; i < argc; ++i) {
        args.emplace_back(argv[i]);
    }

    std::string root = findMultriixRoot();

    // No arguments: launch Multriix directly!
    if (args.empty()) {
        return launchMultriix(root, false);
    }

    const std::string& cmd = args[0];

    if (cmd == "help" || cmd == "--help" || cmd == "-h") {
        printHelp();
        return 0;
    }

    if (cmd == "run") {
        bool legacy = false;
        for (size_t i = 1; i < args.size(); ++i) {
            if (args[i] == "--legacy") legacy = true;
        }
        return launchMultriix(root, legacy);
    }

    if (cmd == "status") {
        printBanner();
        return executeBridge(root, {"status"});
    }

    if (cmd == "save") {
        std::vector<std::string> bArgs = {"save"};
        if (args.size() > 1) bArgs.push_back(args[1]);
        for (size_t i = 2; i < args.size(); ++i) {
            bArgs.push_back(args[i]);
        }
        return executeBridge(root, bArgs);
    }

    if (cmd == "qs") {
        return executeBridge(root, {"save", "quicksave", "-d", "QuickSave Checkpoint"});
    }

    if (cmd == "ql") {
        return executeBridge(root, {"load", "quicksave"});
    }

    if (cmd == "load") {
        if (args.size() < 2) {
            std::cerr << Color::YELLOW << "Usage: mx load <slot_name_or_path> [--merge]" << Color::RESET << std::endl;
            return 1;
        }
        std::vector<std::string> bArgs = {"load", args[1]};
        for (size_t i = 2; i < args.size(); ++i) {
            bArgs.push_back(args[i]);
        }
        return executeBridge(root, bArgs);
    }

    if (cmd == "saves" || cmd == "list") {
        return executeBridge(root, {"list"});
    }

    if (cmd == "info") {
        if (args.size() < 2) {
            std::cerr << Color::YELLOW << "Usage: mx info <file.mxsave>" << Color::RESET << std::endl;
            return 1;
        }
        return executeBridge(root, {"info", args[1]});
    }

    if (cmd == "export") {
        if (args.size() < 3) {
            std::cerr << Color::YELLOW << "Usage: mx export <slot_name> <destination_path.mxsave>" << Color::RESET << std::endl;
            return 1;
        }
        return executeBridge(root, {"export", args[1], args[2]});
    }

    if (cmd == "import") {
        if (args.size() < 2) {
            std::cerr << Color::YELLOW << "Usage: mx import <source_path.mxsave> [slot_name] [--merge]" << Color::RESET << std::endl;
            return 1;
        }
        std::vector<std::string> bArgs = {"import", args[1]};
        for (size_t i = 2; i < args.size(); ++i) {
            bArgs.push_back(args[i]);
        }
        return executeBridge(root, bArgs);
    }

    if (cmd == "test") {
        printBanner();
        std::cout << Color::CYAN << Color::BOLD << "[TEST] Executing real-time Multriix X verification suite..." << Color::RESET << "\n\n";
        return executeBridge(root, {"test"});
    }

    if (cmd == "version" || cmd == "-v" || cmd == "--version") {
        printBanner();
        std::cout << "  Version : 2.0.0-pro\n"
                  << "  Engine  : C++17 Optimized Native CLI\n"
                  << "  Author  : Pheonix14 / ZeroX\n"
                  << "  Root    : " << root << "\n\n";
        return 0;
    }

    // Default: unknown argument, print warning & help
    std::cerr << Color::RED << "Unknown command: '" << cmd << "'" << Color::RESET << "\n\n";
    printHelp();
    return 1;
}
