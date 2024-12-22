RTOS Minimal VGA driver

This minimal VGA driver is designed specifically for an RTOS environment with several key features:

1. **Bare Metal Ready**:
   - No dependencies on standard library functions
   - Direct memory access using volatile pointers
   - All functions are inline for efficiency

2. **RTOS-Friendly**:
   - No dynamic memory allocation
   - Deterministic execution time for all operations
   - Minimal stack usage

3. **Basic Features**:
   - Character writing
   - String output
   - Screen clearing
   - Basic cursor management
   - Color support

Some important considerations for RTOS integration:

1. **Thread Safety**: You'll need to add mutex protection if multiple tasks might access the VGA buffer.

2. **Memory Barriers**: Depending on your architecture, you might need to add memory barriers for the volatile accesses.

3. **Boot Integration**: You'll want to call `vga_clear()` during your boot sequence.

```c
#ifndef VGA_H
#define VGA_H

#include <stdint.h>

// VGA buffer constants
#define VGA_BUFFER_ADDR 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25
#define VGA_SIZE (VGA_WIDTH * VGA_HEIGHT)

// VGA colors
enum vga_color {
    VGA_BLACK = 0,
    VGA_BLUE = 1,
    VGA_GREEN = 2,
    VGA_CYAN = 3,
    VGA_RED = 4,
    VGA_MAGENTA = 5,
    VGA_BROWN = 6,
    VGA_LIGHT_GREY = 7,
    VGA_DARK_GREY = 8,
    VGA_LIGHT_BLUE = 9,
    VGA_LIGHT_GREEN = 10,
    VGA_LIGHT_CYAN = 11,
    VGA_LIGHT_RED = 12,
    VGA_LIGHT_MAGENTA = 13,
    VGA_LIGHT_BROWN = 14,
    VGA_WHITE = 15,
};

// VGA entry structure
typedef struct {
    uint8_t character;
    uint8_t color;
} __attribute__((packed)) vga_entry_t;

// Global VGA buffer pointer
static volatile vga_entry_t* const VGA_BUFFER = (vga_entry_t*)VGA_BUFFER_ADDR;

// Current cursor position
static uint8_t cursor_x = 0;
static uint8_t cursor_y = 0;

// Create a VGA entry
static inline uint16_t vga_entry(char c, uint8_t fg, uint8_t bg) {
    return (uint16_t)c | ((uint16_t)((bg << 4) | (fg & 0x0F)) << 8);
}

// Clear the screen
static inline void vga_clear(void) {
    for (size_t i = 0; i < VGA_SIZE; i++) {
        VGA_BUFFER[i].character = ' ';
        VGA_BUFFER[i].color = vga_entry(0, VGA_LIGHT_GREY, VGA_BLACK) >> 8;
    }
    cursor_x = cursor_y = 0;
}

// Write a character to the current cursor position
static inline void vga_putchar(char c, uint8_t fg, uint8_t bg) {
    if (c == '\n') {
        cursor_x = 0;
        cursor_y++;
        if (cursor_y >= VGA_HEIGHT) {
            cursor_y = 0;  // Wrap around for simplicity
        }
        return;
    }

    size_t index = cursor_y * VGA_WIDTH + cursor_x;
    VGA_BUFFER[index].character = c;
    VGA_BUFFER[index].color = ((bg << 4) | (fg & 0x0F));

    if (++cursor_x >= VGA_WIDTH) {
        cursor_x = 0;
        if (++cursor_y >= VGA_HEIGHT) {
            cursor_y = 0;  // Wrap around for simplicity
        }
    }
}

// Write a string to the current cursor position
static inline void vga_puts(const char* str, uint8_t fg, uint8_t bg) {
    while (*str) {
        vga_putchar(*str++, fg, bg);
    }
}

#endif // VGA_H

```
