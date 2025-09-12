#ifndef TEST_HARNESS_H
#define TEST_HARNESS_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Include LVGL headers for proper type definitions
#ifdef HAVE_LVGL
    #include "lvgl/lvgl.h"
#else
    // Forward declarations for when LVGL is not available
    typedef void* lv_obj_t;
#endif

// Widget registry functions
int reg_widget(const char *id, lv_obj_t *obj);
lv_obj_t *find_widget(const char *id);
void cleanup_registry(void);
void print_registry(void);

// Test harness API
int test_click(const char *id);
int test_longpress(const char *id, uint32_t ms);
int test_swipe(int x1, int y1, int x2, int y2);
int test_key_event(int code);
char* test_get_text(const char *id);
int test_set_text(const char *id, const char *text);
int test_screenshot(uint8_t **png_data, size_t *png_len);
void test_wait(uint32_t ms);

// Helper functions for input emulation
void emulate_click_at(int x, int y);
void emulate_longpress_at(int x, int y, uint32_t ms);
void emulate_swipe_gesture(int x1, int y1, int x2, int y2);

// Initialization
int init_test_system(void);
int test_harness_init(void);
void test_harness_cleanup(void);

// TCP server functions
int tcp_server_init(int port);
void tcp_server_cleanup(void);
int tcp_server_start(void);

// Screenshot functions
int screenshot_init(void);
void screenshot_cleanup(void);
int capture_screenshot(uint8_t **png_data, size_t *png_len);

// Constants
#define MAX_WIDGETS 64
#define MAX_ID_LEN 32
#define DEFAULT_PORT 12345
#define MAX_COMMAND_LEN 1024
#define MAX_COMMAND_QUEUE 32

// Error codes
#define TEST_OK 0
#define TEST_ERROR_NOT_FOUND -1
#define TEST_ERROR_INVALID_PARAM -2
#define TEST_ERROR_MEMORY -3
#define TEST_ERROR_NETWORK -4
#define TEST_ERROR_SCREENSHOT -5
#define TEST_ERROR_QUEUE_FULL -6
#define TEST_ERROR_INVALID_WIDGET -7
#define TEST_ERROR_EVENT_FAILED -8

// UI functions
void ui_watch_create(void);
void ui_watch_update(void);

// Command queue structures
typedef enum {
    CMD_CLICK,
    CMD_LONGPRESS,
    CMD_SWIPE,
    CMD_KEY_EVENT,
    CMD_GET_TEXT,
    CMD_SET_TEXT,
    CMD_SCREENSHOT,
    CMD_WAIT
} command_type_t;

typedef struct {
    command_type_t type;
    char widget_id[MAX_ID_LEN];
    union {
        struct { uint32_t ms; } longpress;
        struct { int x1, y1, x2, y2; } swipe;
        struct { int code; } key;
        struct { char text[MAX_COMMAND_LEN]; } set_text;
        struct { uint32_t ms; } wait;
    } params;
    
    // Response fields
    char *response_text;
    uint8_t *response_data;
    size_t response_len;
    int result;
    volatile int completed;
} command_t;

// Command queue functions
int command_queue_init(void);
void command_queue_cleanup(void);
int command_queue_push(command_t *cmd);
int command_queue_process_all(void);

#ifdef __cplusplus
}
#endif

#endif // TEST_HARNESS_H