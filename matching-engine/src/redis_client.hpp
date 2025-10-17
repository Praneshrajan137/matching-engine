#ifndef REDIS_CLIENT_HPP
#define REDIS_CLIENT_HPP

#include <string>
#include <vector>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdexcept>
#include <sstream>
#include <iostream>

#pragma comment(lib, "ws2_32.lib")

/**
 * Lightweight Redis client for Windows
 * Implements BLPOP and PUBLISH commands using Redis protocol (RESP)
 * 
 * Design: Minimal, fast, zero external dependencies
 */
class RedisClient {
public:
    RedisClient(const std::string& host = "127.0.0.1", int port = 6379)
        : host_(host), port_(port), socket_(INVALID_SOCKET) {
        // Initialize Winsock
        WSADATA wsaData;
        int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
        if (result != 0) {
            throw std::runtime_error("WSAStartup failed: " + std::to_string(result));
        }
    }

    ~RedisClient() {
        disconnect();
        WSACleanup();
    }

    // Connect to Redis server
    bool connect() {
        // Create socket
        socket_ = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (socket_ == INVALID_SOCKET) {
            std::cerr << "Failed to create socket: " << WSAGetLastError() << std::endl;
            return false;
        }

        // Setup server address
        sockaddr_in serverAddr;
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_port = htons(port_);
        inet_pton(AF_INET, host_.c_str(), &serverAddr.sin_addr);

        // Connect
        if (::connect(socket_, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
            std::cerr << "Failed to connect to Redis: " << WSAGetLastError() << std::endl;
            closesocket(socket_);
            socket_ = INVALID_SOCKET;
            return false;
        }

        std::cout << "Connected to Redis at " << host_ << ":" << port_ << std::endl;
        return true;
    }

    // Disconnect from Redis
    void disconnect() {
        if (socket_ != INVALID_SOCKET) {
            closesocket(socket_);
            socket_ = INVALID_SOCKET;
        }
    }

    // BLPOP: Blocking left pop from list (for consuming orders)
    // Returns empty string if timeout or error
    std::string blpop(const std::string& queue_name, int timeout_seconds = 1) {
        if (socket_ == INVALID_SOCKET) {
            return "";
        }

        // Build RESP command: BLPOP queue_name timeout
        std::string command = build_resp_array({
            "BLPOP",
            queue_name,
            std::to_string(timeout_seconds)
        });

        // Send command
        if (send_command(command) != command.length()) {
            return "";
        }

        // Read response
        std::string response = read_response();
        
        // Parse BLPOP response
        // Format: *2\r\n$<len>\r\n<queue_name>\r\n$<len>\r\n<data>\r\n
        // or: $-1\r\n (null, timeout)
        
        if (response.empty() || response[0] == '$') {
            // Null response or error
            return "";
        }

        // Extract the data part (second element of array)
        return parse_blpop_response(response);
    }

    // PUBLISH: Publish message to channel (for broadcasting trades)
    bool publish(const std::string& channel, const std::string& message) {
        if (socket_ == INVALID_SOCKET) {
            return false;
        }

        // Build RESP command: PUBLISH channel message
        std::string command = build_resp_array({
            "PUBLISH",
            channel,
            message
        });

        // Send command
        if (send_command(command) != command.length()) {
            return false;
        }

        // Read response (integer reply with number of subscribers)
        std::string response = read_response();
        return !response.empty() && response[0] == ':';
    }

    // PING: Test connection
    bool ping() {
        if (socket_ == INVALID_SOCKET) {
            return false;
        }

        std::string command = build_resp_array({"PING"});
        if (send_command(command) != command.length()) {
            return false;
        }

        std::string response = read_response();
        return response.find("PONG") != std::string::npos;
    }

private:
    std::string host_;
    int port_;
    SOCKET socket_;

    // Build Redis RESP array command
    std::string build_resp_array(const std::vector<std::string>& parts) {
        std::ostringstream oss;
        oss << "*" << parts.size() << "\r\n";
        for (const auto& part : parts) {
            oss << "$" << part.length() << "\r\n";
            oss << part << "\r\n";
        }
        return oss.str();
    }

    // Send command to Redis
    int send_command(const std::string& command) {
        return send(socket_, command.c_str(), static_cast<int>(command.length()), 0);
    }

    // Read response from Redis
    std::string read_response() {
        char buffer[4096];
        int bytes = recv(socket_, buffer, sizeof(buffer) - 1, 0);
        if (bytes > 0) {
            buffer[bytes] = '\0';
            return std::string(buffer, bytes);
        }
        return "";
    }

    // Parse BLPOP response to extract data
    std::string parse_blpop_response(const std::string& response) {
        // BLPOP returns: *2\r\n$<len>\r\n<queue_name>\r\n$<len>\r\n<data>\r\n
        
        // Find the second bulk string (the data)
        size_t pos = 0;
        int bulk_count = 0;
        
        while (pos < response.length() && bulk_count < 2) {
            if (response[pos] == '$') {
                // Found bulk string marker
                size_t len_start = pos + 1;
                size_t len_end = response.find("\r\n", len_start);
                if (len_end == std::string::npos) break;
                
                int length = std::stoi(response.substr(len_start, len_end - len_start));
                if (length < 0) return ""; // Null bulk string
                
                size_t data_start = len_end + 2;
                if (bulk_count == 1) {
                    // This is the data we want
                    return response.substr(data_start, length);
                }
                
                pos = data_start + length + 2; // Skip past this bulk string
                bulk_count++;
            } else {
                pos++;
            }
        }
        
        return "";
    }
};

#endif // REDIS_CLIENT_HPP

