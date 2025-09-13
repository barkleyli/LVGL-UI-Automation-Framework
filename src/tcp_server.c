#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    #define close closesocket
    #define ssize_t int
    #define usleep(x) Sleep((x)/1000)
#else
    #include <unistd.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #define INVALID_SOCKET -1
    #define SOCKET_ERROR -1
    #define SOCKET int
#endif

#include "test_harness.h"

// JSON parsing (simple implementation for this prototype)
#include <ctype.h>

// Server state
static struct {
    SOCKET server_socket;
    SOCKET client_socket;
    struct sockaddr_in server_addr;
    int port;
    volatile int running;
    volatile int client_connected;
} tcp_server = {0};

// JSON parsing helpers
typedef struct {
    char *data;
    size_t pos;
    size_t len;
} json_parser_t;

static void skip_whitespace(json_parser_t *parser) {
    while (parser->pos < parser->len && isspace(parser->data[parser->pos])) {
        parser->pos++;
    }
}

static int parse_string(json_parser_t *parser, char *out, size_t max_len) {
    skip_whitespace(parser);
    if (parser->pos >= parser->len || parser->data[parser->pos] != '"') {
        return -1;
    }
    
    parser->pos++; // skip opening quote
    size_t start = parser->pos;
    
    while (parser->pos < parser->len && parser->data[parser->pos] != '"') {
        parser->pos++;
    }
    
    if (parser->pos >= parser->len) {
        return -1; // unterminated string
    }
    
    size_t len = parser->pos - start;
    if (len >= max_len) {
        len = max_len - 1;
    }
    
    memcpy(out, &parser->data[start], len);
    out[len] = '\0';
    
    parser->pos++; // skip closing quote
    return 0;
}

static int parse_int(json_parser_t *parser) {
    skip_whitespace(parser);
    if (parser->pos >= parser->len || !isdigit(parser->data[parser->pos])) {
        return -1;
    }
    
    int value = 0;
    while (parser->pos < parser->len && isdigit(parser->data[parser->pos])) {
        value = value * 10 + (parser->data[parser->pos] - '0');
        parser->pos++;
    }
    
    return value;
}

static int find_key(json_parser_t *parser, const char *key) {
    char current_key[64];
    
    // Reset to beginning
    parser->pos = 0;
    skip_whitespace(parser);
    
    if (parser->pos >= parser->len || parser->data[parser->pos] != '{') {
        return -1;
    }
    
    parser->pos++; // skip opening brace
    
    while (parser->pos < parser->len) {
        skip_whitespace(parser);
        
        if (parser->data[parser->pos] == '}') {
            break; // end of object
        }
        
        // Parse key
        if (parse_string(parser, current_key, sizeof(current_key)) != 0) {
            return -1;
        }
        
        skip_whitespace(parser);
        if (parser->pos >= parser->len || parser->data[parser->pos] != ':') {
            return -1;
        }
        parser->pos++; // skip colon
        
        if (strcmp(current_key, key) == 0) {
            return 0; // found key, parser is positioned at value
        }
        
        // Skip value (simple implementation)
        skip_whitespace(parser);
        if (parser->data[parser->pos] == '"') {
            // Skip string value
            parser->pos++;
            while (parser->pos < parser->len && parser->data[parser->pos] != '"') {
                parser->pos++;
            }
            parser->pos++;
        } else if (isdigit(parser->data[parser->pos]) || parser->data[parser->pos] == '-') {
            // Skip number value
            if (parser->data[parser->pos] == '-') parser->pos++;
            while (parser->pos < parser->len && (isdigit(parser->data[parser->pos]) || parser->data[parser->pos] == '.')) {
                parser->pos++;
            }
        }
        
        // Skip comma
        skip_whitespace(parser);
        if (parser->pos < parser->len && parser->data[parser->pos] == ',') {
            parser->pos++;
        }
    }
    
    return -1; // key not found
}

// Command processing
static void send_response(SOCKET client, const char *response) {
    size_t len = strlen(response);
    ssize_t sent = send(client, response, (int)len, 0);
    if (sent != (ssize_t)len) {
        printf("Failed to send complete response\n");
    }
    printf("Sent response: %s\n", response);
}

static void send_error_response(SOCKET client, const char *cmd, const char *error) {
    char response[256];
    snprintf(response, sizeof(response), 
             "{\"status\":\"error\",\"cmd\":\"%s\",\"error\":\"%s\"}\n", 
             cmd ? cmd : "unknown", error);
    send_response(client, response);
}

static void send_ok_response(SOCKET client, const char *cmd) {
    char response[128];
    snprintf(response, sizeof(response), "{\"status\":\"ok\",\"cmd\":\"%s\"}\n", cmd);
    send_response(client, response);
}

static void process_command(SOCKET client, const char *json_cmd) {
    printf("Processing command: %s\n", json_cmd);
    
    json_parser_t parser = {0};
    parser.data = (char*)json_cmd;
    parser.len = strlen(json_cmd);
    
    // Parse command type
    char cmd[32] = {0};
    if (find_key(&parser, "cmd") != 0 || parse_string(&parser, cmd, sizeof(cmd)) != 0) {
        send_error_response(client, NULL, "invalid_json");
        return;
    }
    
    // Process different command types - direct calls for now
    if (strcmp(cmd, "click") == 0) {
        char id[64] = {0};
        if (find_key(&parser, "id") != 0 || parse_string(&parser, id, sizeof(id)) != 0) {
            send_error_response(client, cmd, "missing_id");
            return;
        }
        
        int result = test_click(id);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "widget_not_found");
        }
        
    } else if (strcmp(cmd, "longpress") == 0) {
        char id[64] = {0};
        if (find_key(&parser, "id") != 0 || parse_string(&parser, id, sizeof(id)) != 0) {
            send_error_response(client, cmd, "missing_id");
            return;
        }
        
        int ms = 1000; // default
        if (find_key(&parser, "ms") == 0) {
            ms = parse_int(&parser);
            if (ms <= 0) ms = 1000;
        }
        
        int result = test_longpress(id, ms);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "widget_not_found");
        }
        
    } else if (strcmp(cmd, "swipe") == 0) {
        int x1, y1, x2, y2;
        
        if (find_key(&parser, "x1") != 0 || (x1 = parse_int(&parser)) < 0 ||
            find_key(&parser, "y1") != 0 || (y1 = parse_int(&parser)) < 0 ||
            find_key(&parser, "x2") != 0 || (x2 = parse_int(&parser)) < 0 ||
            find_key(&parser, "y2") != 0 || (y2 = parse_int(&parser)) < 0) {
            send_error_response(client, cmd, "invalid_coordinates");
            return;
        }
        
        int result = test_swipe(x1, y1, x2, y2);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "swipe_failed");
        }
        
    } else if (strcmp(cmd, "key") == 0) {
        int code;
        if (find_key(&parser, "code") != 0 || (code = parse_int(&parser)) < 0) {
            send_error_response(client, cmd, "invalid_key_code");
            return;
        }
        
        int result = test_key_event(code);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "key_event_failed");
        }
        
    } else if (strcmp(cmd, "get_state") == 0) {
        char id[64] = {0};
        if (find_key(&parser, "id") != 0 || parse_string(&parser, id, sizeof(id)) != 0) {
            send_error_response(client, cmd, "missing_id");
            return;
        }
        
        char *text = test_get_text(id);
        if (text) {
            char response[512];
            snprintf(response, sizeof(response), 
                     "{\"status\":\"ok\",\"cmd\":\"%s\",\"text\":\"%s\"}\n", 
                     cmd, text);
            send_response(client, response);
            free(text);
        } else {
            send_error_response(client, cmd, "widget_not_found");
        }
        
    } else if (strcmp(cmd, "set_text") == 0) {
        char id[64] = {0};
        char text[256] = {0};
        
        if (find_key(&parser, "id") != 0 || parse_string(&parser, id, sizeof(id)) != 0 ||
            find_key(&parser, "text") != 0 || parse_string(&parser, text, sizeof(text)) != 0) {
            send_error_response(client, cmd, "missing_parameters");
            return;
        }
        
        int result = test_set_text(id, text);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "widget_not_found");
        }
        
    } else if (strcmp(cmd, "screenshot") == 0) {
        uint8_t *raw_data = NULL;
        size_t raw_len = 0;
        
        int result = test_screenshot(&raw_data, &raw_len);
        if (result == TEST_OK && raw_data && raw_len > 0) {
            // Send JSON header with PNG format information 
            char header[256];
            snprintf(header, sizeof(header), 
                     "{\"status\":\"ok\",\"type\":\"screenshot\",\"width\":%d,\"height\":%d,\"format\":\"PNG\",\"len\":%zu}\n", 
                     480, 480, raw_len);  // Using the actual display dimensions
            send_response(client, header);
            
            // Send PNG data
            ssize_t sent = send(client, (char*)raw_data, (int)raw_len, 0);
            if (sent != (ssize_t)raw_len) {
                printf("Failed to send complete PNG screenshot data\n");
            } else {
                printf("PNG screenshot sent: %zu bytes (%dx%d)\n", raw_len, 480, 480);
            }
            
            free(raw_data);
        } else {
            printf("Screenshot failed with result: %d\n", result);
            send_error_response(client, cmd, "screenshot_failed");
        }
        
    } else if (strcmp(cmd, "wait") == 0) {
        int ms = 100; // default
        if (find_key(&parser, "ms") == 0) {
            ms = parse_int(&parser);
            if (ms <= 0) ms = 100;
        }
        
        test_wait(ms);
        send_ok_response(client, cmd);
        
    } else if (strcmp(cmd, "click_at") == 0) {
        int x, y;
        if (find_key(&parser, "x") != 0 || (x = parse_int(&parser)) < 0 ||
            find_key(&parser, "y") != 0 || (y = parse_int(&parser)) < 0) {
            send_error_response(client, cmd, "invalid_coordinates");
            return;
        }
        
        int result = test_click_at(x, y);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "click_failed");
        }
        
    } else if (strcmp(cmd, "mouse_move") == 0) {
        int x, y;
        if (find_key(&parser, "x") != 0 || (x = parse_int(&parser)) < 0 ||
            find_key(&parser, "y") != 0 || (y = parse_int(&parser)) < 0) {
            send_error_response(client, cmd, "invalid_coordinates");
            return;
        }
        
        int result = test_mouse_move(x, y);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "mouse_move_failed");
        }
        
    } else if (strcmp(cmd, "drag") == 0) {
        int x1, y1, x2, y2;
        if (find_key(&parser, "x1") != 0 || (x1 = parse_int(&parser)) < 0 ||
            find_key(&parser, "y1") != 0 || (y1 = parse_int(&parser)) < 0 ||
            find_key(&parser, "x2") != 0 || (x2 = parse_int(&parser)) < 0 ||
            find_key(&parser, "y2") != 0 || (y2 = parse_int(&parser)) < 0) {
            send_error_response(client, cmd, "invalid_coordinates");
            return;
        }
        
        int result = test_drag(x1, y1, x2, y2);
        if (result == TEST_OK) {
            send_ok_response(client, cmd);
        } else {
            send_error_response(client, cmd, "drag_failed");
        }
        
    } else {
        send_error_response(client, cmd, "unknown_command");
    }
}

// Network functions
int tcp_server_init(int port) {
    printf("Initializing TCP server on port %d...\n", port);
    
#ifdef _WIN32
    WSADATA wsaData;
    int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (result != 0) {
        printf("WSAStartup failed: %d\n", result);
        return TEST_ERROR_NETWORK;
    }
#endif
    
    tcp_server.server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_server.server_socket == INVALID_SOCKET) {
        printf("Failed to create socket: %s\n", strerror(errno));
#ifdef _WIN32
        WSACleanup();
#endif
        return TEST_ERROR_NETWORK;
    }
    
    // Set socket options
    int opt = 1;
    if (setsockopt(tcp_server.server_socket, SOL_SOCKET, SO_REUSEADDR, 
                   (char*)&opt, sizeof(opt)) < 0) {
        printf("Failed to set socket options\n");
    }
    
    // Bind to port
    memset(&tcp_server.server_addr, 0, sizeof(tcp_server.server_addr));
    tcp_server.server_addr.sin_family = AF_INET;
    tcp_server.server_addr.sin_addr.s_addr = INADDR_ANY;
    tcp_server.server_addr.sin_port = htons(port);
    
    if (bind(tcp_server.server_socket, (struct sockaddr*)&tcp_server.server_addr, 
             sizeof(tcp_server.server_addr)) < 0) {
        printf("Failed to bind socket: %s\n", strerror(errno));
        close(tcp_server.server_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return TEST_ERROR_NETWORK;
    }
    
    // Listen for connections
    if (listen(tcp_server.server_socket, 1) < 0) {
        printf("Failed to listen on socket: %s\n", strerror(errno));
        close(tcp_server.server_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return TEST_ERROR_NETWORK;
    }
    
    tcp_server.port = port;
    tcp_server.running = 1;
    tcp_server.client_connected = 0;
    
    printf("TCP server initialized on port %d\n", port);
    return TEST_OK;
}

void tcp_server_cleanup(void) {
    printf("Cleaning up TCP server...\n");
    
    tcp_server.running = 0;
    
    if (tcp_server.client_socket != INVALID_SOCKET) {
        close(tcp_server.client_socket);
        tcp_server.client_socket = INVALID_SOCKET;
    }
    
    if (tcp_server.server_socket != INVALID_SOCKET) {
        close(tcp_server.server_socket);
        tcp_server.server_socket = INVALID_SOCKET;
    }
    
#ifdef _WIN32
    WSACleanup();
#endif
    
    tcp_server.client_connected = 0;
    printf("TCP server cleanup complete\n");
}

int tcp_server_start(void) {
    printf("TCP server starting main loop...\n");
    
    while (tcp_server.running) {
        printf("Waiting for client connection on port %d...\n", tcp_server.port);
        
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        
        tcp_server.client_socket = accept(tcp_server.server_socket, 
                                         (struct sockaddr*)&client_addr, 
                                         &client_len);
        
        if (tcp_server.client_socket == INVALID_SOCKET) {
            if (tcp_server.running) {
                printf("Failed to accept connection: %s\n", strerror(errno));
            }
            continue;
        }
        
        tcp_server.client_connected = 1;
        printf("Client connected from %s:%d\n", 
               inet_ntoa(client_addr.sin_addr), 
               ntohs(client_addr.sin_port));
        
        // Handle client commands
        char buffer[MAX_COMMAND_LEN];
        while (tcp_server.running && tcp_server.client_connected) {
            ssize_t bytes_received = recv(tcp_server.client_socket, buffer, 
                                        sizeof(buffer) - 1, 0);
            
            if (bytes_received <= 0) {
                printf("Client disconnected\n");
                tcp_server.client_connected = 0;
                break;
            }
            
            buffer[bytes_received] = '\0';
            
            // Process each line (commands are newline-terminated)
            char *line = strtok(buffer, "\n");
            while (line && tcp_server.running) {
                // Trim whitespace
                while (isspace(*line)) line++;
                if (strlen(line) > 0) {
                    process_command(tcp_server.client_socket, line);
                }
                line = strtok(NULL, "\n");
            }
        }
        
        close(tcp_server.client_socket);
        tcp_server.client_socket = INVALID_SOCKET;
        tcp_server.client_connected = 0;
    }
    
    printf("TCP server main loop ended\n");
    return TEST_OK;
}