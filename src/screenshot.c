#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

// Check if we have LVGL available
#ifdef HAVE_LVGL
    #include "lvgl/lvgl.h"
    #include "third_party/lvgl/src/others/snapshot/lv_snapshot.h"
#else
    // Fallback stubs for initial build without LVGL
    typedef void* lv_display_t;
    typedef struct lv_draw_buf_t {
        void* data;
    } lv_draw_buf_t;
    typedef uint32_t lv_color_t;
    typedef int lv_coord_t;
    #define lv_display_get_default() (NULL)
    #define lv_display_get_buf_active(disp) (NULL)
    #define lv_color_to_32(c, opa) (0xFF0000FF)
#endif

// Include stb_image_write for PNG encoding (LVGL v9 compatible)
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "third_party/stb/stb_image_write.h"

#include "test_harness.h"

// Screenshot configuration - match display size
#define SCREENSHOT_WIDTH 480
#define SCREENSHOT_HEIGHT 480
#define SCREENSHOT_CHANNELS 3  // RGB

// Global screenshot state
static struct {
    uint8_t *rgb_buffer;
    size_t buffer_size;
    int initialized;
} screenshot_state = {0};

// Capture screenshot - returns PNG data directly from main display
int capture_screenshot(uint8_t **raw_data, size_t *raw_len) {
    printf("Capturing screenshot directly from main display...\n");
    
    if (!raw_data || !raw_len) {
        printf("Invalid parameters: raw_data=%p, raw_len=%p\n", (void*)raw_data, (void*)raw_len);
        return TEST_ERROR_INVALID_PARAM;
    }
    
    *raw_data = NULL;
    *raw_len = 0;
    
    if (!screenshot_state.initialized) {
        printf("Screenshot system not initialized\n");
        return TEST_ERROR_SCREENSHOT;
    }

#ifdef HAVE_LVGL
    // Get the main display directly (no test display needed)
    lv_display_t *main_disp = lv_display_get_default();
    if (!main_disp) {
        printf("No main display found\n");
        return TEST_ERROR_SCREENSHOT;
    }
    
    // Force refresh to ensure current state is rendered
    lv_refr_now(main_disp);
    
    // Take snapshot directly from the active screen on main display
    lv_draw_buf_t *snapshot_buf = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_ARGB8888);
    if (!snapshot_buf) {
        printf("Failed to take snapshot\n");
        return TEST_ERROR_SCREENSHOT;
    }
    
    printf("Snapshot taken successfully\n");
    
    // Get buffer dimensions and data
    uint32_t buf_width = snapshot_buf->header.w;
    uint32_t buf_height = snapshot_buf->header.h;
    uint8_t *argb_data = (uint8_t*)snapshot_buf->data;
    
    printf("Snapshot size: %dx%d, data=%p\n", buf_width, buf_height, (void*)argb_data);
    
    if (!argb_data || buf_width == 0 || buf_height == 0) {
        printf("Invalid snapshot data\n");
        lv_draw_buf_destroy(snapshot_buf);
        return TEST_ERROR_SCREENSHOT;
    }
    
    // Convert ARGB to RGB for PNG encoding
    size_t rgb_size = buf_width * buf_height * 3;
    uint8_t *rgb_buffer = malloc(rgb_size);
    if (!rgb_buffer) {
        printf("Failed to allocate RGB buffer\n");
        lv_draw_buf_destroy(snapshot_buf);
        return TEST_ERROR_MEMORY;
    }
    
    // Convert ARGB8888 to RGB24
    for (uint32_t i = 0; i < buf_width * buf_height; i++) {
        uint32_t argb = ((uint32_t*)argb_data)[i];
        rgb_buffer[i*3 + 0] = (argb >> 16) & 0xFF; // Red
        rgb_buffer[i*3 + 1] = (argb >> 8) & 0xFF;  // Green  
        rgb_buffer[i*3 + 2] = argb & 0xFF;         // Blue
    }
    
    // Encode to PNG using stb_image_write
    int png_size;
    unsigned char *png_buffer = stbi_write_png_to_mem(rgb_buffer, buf_width * 3, buf_width, buf_height, 3, &png_size);
    
    free(rgb_buffer);
    lv_draw_buf_destroy(snapshot_buf);
    
    if (!png_buffer || png_size <= 0) {
        printf("Failed to encode PNG\n");
        return TEST_ERROR_SCREENSHOT;
    }
    
    *raw_data = png_buffer;
    *raw_len = png_size;
    
    printf("Screenshot captured successfully: %d bytes\n", png_size);
    return TEST_OK;
#else
    printf("LVGL not available\n");
    return TEST_ERROR_SCREENSHOT;
#endif
}

// Initialize screenshot system
int screenshot_init(void) {
    printf("Initializing screenshot system...\n");
    
    // Allocate RGB buffer for conversions
    screenshot_state.buffer_size = SCREENSHOT_WIDTH * SCREENSHOT_HEIGHT * SCREENSHOT_CHANNELS;
    screenshot_state.rgb_buffer = malloc(screenshot_state.buffer_size);
    
    if (!screenshot_state.rgb_buffer) {
        printf("Failed to allocate screenshot buffer\n");
        return TEST_ERROR_MEMORY;
    }
    
    screenshot_state.initialized = 1;
    
#ifdef HAVE_LVGL
    printf("Screenshot system initialized with LVGL + stb_image_write support\n");
#else
    printf("Screenshot system initialized in stub mode (no LVGL)\n");
#endif
    
    return TEST_OK;
}

// Cleanup screenshot system
void screenshot_cleanup(void) {
    printf("Cleaning up screenshot system...\n");
    
    if (screenshot_state.rgb_buffer) {
        free(screenshot_state.rgb_buffer);
        screenshot_state.rgb_buffer = NULL;
    }
    
    screenshot_state.initialized = 0;
    screenshot_state.buffer_size = 0;
    
    printf("Screenshot system cleanup complete\n");
}