#pragma once

// Fix Windows.h macro conflicts
#ifdef ERROR
#undef ERROR
#endif
#ifdef DEBUG
#undef DEBUG
#endif

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <utility>
#include <chrono>
#include <ctime>

enum class LogLevel { DEBUG, INFO, WARN, ERROR };

namespace logger {

inline const char* level_to_string(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO:  return "INFO";
        case LogLevel::WARN:  return "WARN";
        case LogLevel::ERROR: return "ERROR";
        default: return "INFO";
    }
}

inline std::string now_iso8601() {
    using clock = std::chrono::system_clock;
    auto now = clock::now();
    std::time_t t = clock::to_time_t(now);
    std::tm tm;
#ifdef _WIN32
    localtime_s(&tm, &t);
#else
    localtime_r(&t, &tm);
#endif
    char buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &tm);
    return std::string(buf);
}

inline std::string escape_json(const std::string& s) {
    std::ostringstream o;
    for (char c : s) {
        switch (c) {
            case '"': o << "\\\""; break;
            case '\\': o << "\\\\"; break;
            case '\n': o << "\\n"; break;
            case '\r': o << "\\r"; break;
            case '\t': o << "\\t"; break;
            default: o << c; break;
        }
    }
    return o.str();
}

// fields: vector of key,value (values are written as strings)
inline void log_json(LogLevel level, const std::string& message,
                     const std::vector<std::pair<std::string, std::string>>& fields = {}) {
    std::ostringstream oss;
    oss << "{";
    oss << "\"ts\":\"" << now_iso8601() << "\",";
    oss << "\"level\":\"" << level_to_string(level) << "\",";
    oss << "\"msg\":\"" << escape_json(message) << "\"";
    for (const auto& kv : fields) {
        oss << ",\"" << escape_json(kv.first) << "\":\"" << escape_json(kv.second) << "\"";
    }
    oss << "}";
    const std::string out = oss.str();
    if (level == LogLevel::WARN || level == LogLevel::ERROR) {
        std::cerr << out << std::endl;
    } else {
        std::cout << out << std::endl;
    }
}

} // namespace logger