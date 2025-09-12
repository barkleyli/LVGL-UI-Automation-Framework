#include <stdio.h>
#include <stdlib.h>
#ifdef _WIN32
    #include <windows.h>
    #include <process.h>
    #define usleep(x) Sleep((x)/1000)
    typedef HANDLE pthread_t;
#else
    #include <unistd.h>
    #include <pthread.h>
    #include <signal.h>
#endif

#ifdef HAVE_LVGL
    #include "lvgl/lvgl.h"
    #include "lvgl/src/drivers/sdl/lv_sdl_window.h"
    #include "lvgl/src/drivers/sdl/lv_sdl_mouse.h"
    #include "lvgl/src/drivers/sdl/lv_sdl_keyboard.h"
#else
    // Fallback stubs for initial build without LVGL
    typedef void* lv_disp_t;
    typedef void* lv_indev_t;
    #define lv_init() ((void)0)
    #define lv_disp_drv_init(x) ((void)0)
    #define lv_disp_drv_register(x) (NULL)
    #define lv_indev_drv_init(x) ((void)0)
    #define lv_indev_drv_register(x) (NULL)
    #define lv_timer_handler() ((void)0)
    #define lv_tick_inc(x) ((void)0)
    #define lv_tick_get() (0)
    #define SDL_GetTicks() (0)
    #define LV_DPI_DEF 130
#endif

#include "test_harness.h"

// Global variables
static volatile int running = 1;
static pthread_t tcp_server_thread;

#ifndef _WIN32
// Signal handler for clean shutdown (Unix only)
void signal_handler(int sig) {
    printf("\nShutdown signal received (%d). Cleaning up...\n", sig);
    running = 0;
}
#endif

// TCP server thread function
void* tcp_server_thread_func(void* arg) {
    printf("Starting TCP server thread...\n");
    if (tcp_server_start() != TEST_OK) {
        printf("Failed to start TCP server\n");
        running = 0;
        return NULL;
    }
    return NULL;
}

#ifdef HAVE_LVGL
// Use official LVGL SDL driver instead of our broken implementation
static lv_display_t *display;
static lv_indev_t *mouse_indev;
// Removed keyboard - only mouse needed for click/longpress/swipe

// Initialize LVGL with official SDL driver
int lvgl_init(void) {
    // Initialize LVGL
    lv_init();
    
    // Create SDL window using official LVGL driver
    display = lv_sdl_window_create(480, 480);
    if (display == NULL) {
        printf("Failed to create SDL window with LVGL driver\n");
        return -1;
    }
    
    // Color format handled automatically by SDL driver
    // SDL driver automatically detects optimal color format
    printf("Using default color format from SDL driver\n");
    
    // Create mouse input device
    mouse_indev = lv_sdl_mouse_create();
    if (mouse_indev == NULL) {
        printf("Failed to create SDL mouse input device\n");
        return -1;
    }
    
    // Set longpress timeout for manual use
    lv_indev_set_long_press_time(mouse_indev, 1000);  // 1 second for manual longpress
    printf("Mouse longpress timeout set to 1000ms for manual use\n");
    
    // Note: Gesture recognition is enabled by default in LVGL v9
    printf("Mouse gesture recognition ready for swipe detection\n");
    
    // Keyboard not needed - automation uses TCP commands for click/longpress/swipe
    
    lv_sdl_window_set_title(display, "LVGL Watch Simulator");
    printf("LVGL SDL window created successfully\n");
    printf("LVGL SDL mouse input device created\n");
    
    return 0;
}

// Official LVGL SDL driver handles all callbacks automatically

#endif

int main(void) {
    printf("LVGL UI Automation Framework Starting...\n");
    printf("=========================================\n");
    
    // Set up signal handlers for clean shutdown (Unix only)
#ifndef _WIN32
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
#endif
    
    // Initialize test harness
    if (test_harness_init() != TEST_OK) {
        printf("Failed to initialize test harness\n");
        return 1;
    }
    
#if HAVE_LVGL
    // Initialize LVGL
    if (lvgl_init() != 0) {
        printf("Failed to initialize LVGL\n");
        test_harness_cleanup();
        return 1;
    }
    
    // Initialize LVGL test system (after LVGL is ready)
    if (init_test_system() != TEST_OK) {
        printf("Failed to initialize LVGL test system\n");
        test_harness_cleanup();
        return 1;
    }
    
    // Create the watch UI
    ui_watch_create();
    printf("Watch UI created\n");
    
    // Force initial screen refresh
    lv_obj_invalidate(lv_screen_active());
    lv_refr_now(NULL);
#else
    printf("Warning: LVGL not available, running in stub mode\n");
    printf("To enable LVGL:\n");
    printf("1. Clone LVGL: git submodule add https://github.com/lvgl/lvgl.git third_party/lvgl\n");
    printf("2. Rebuild the project\n");
#endif
    
    // Initialize screenshot system
    if (screenshot_init() != TEST_OK) {
        printf("Failed to initialize screenshot system\n");
    }
    
    // Initialize and start TCP server
    if (tcp_server_init(DEFAULT_PORT) != TEST_OK) {
        printf("Failed to initialize TCP server on port %d\n", DEFAULT_PORT);
        return 1;
    }
    
    // Start TCP server in separate thread
#ifdef _WIN32
    tcp_server_thread = (HANDLE)_beginthreadex(NULL, 0, 
        (unsigned (__stdcall *)(void *))tcp_server_thread_func, NULL, 0, NULL);
    if (tcp_server_thread == 0) {
#else
    if (pthread_create(&tcp_server_thread, NULL, tcp_server_thread_func, NULL) != 0) {
#endif
        printf("Failed to create TCP server thread\n");
        tcp_server_cleanup();
        test_harness_cleanup();
        return 1;
    }
    
    printf("TCP server listening on port %d\n", DEFAULT_PORT);
    printf("Ready for automation commands\n");
    printf("Press Ctrl+C to quit\n");
    
    // Main loop - let LVGL handle everything
    while (running) {
        // Handle LVGL tasks (includes SDL events automatically)
        lv_timer_handler();
        
        // Process any queued commands on LVGL thread
        command_queue_process_all();
        
        // Small delay to prevent busy waiting
        usleep(5000); // 5ms
    }
    
    printf("Shutting down...\n");
    
    // Clean shutdown
#ifdef _WIN32
    TerminateThread(tcp_server_thread, 0);
    WaitForSingleObject(tcp_server_thread, INFINITE);
    CloseHandle(tcp_server_thread);
#else
    pthread_cancel(tcp_server_thread);
    pthread_join(tcp_server_thread, NULL);
#endif
    
    tcp_server_cleanup();
    screenshot_cleanup();
    test_harness_cleanup();
    
#ifdef HAVE_LVGL
    // LVGL cleanup (official driver handles SDL cleanup automatically)
    lv_deinit();
#endif
    
    printf("Cleanup complete. Goodbye!\n");
    return 0;
}