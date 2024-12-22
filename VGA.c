#ifndef VGA_H
#define VGA_H

#include <stdint.h>
#include <stddef.h>

// VGA buffer constants
#define VGA_BUFFER_ADDR 0xB8000
#define VGA_WIDTH 80
#define VGA_HEIGHT 25
#define VGA_SIZE (VGA_WIDTH * VGA_HEIGHT)

// VGA I/O ports
#define VGA_CTRL_PORT 0x3D4
#define VGA_DATA_PORT 0x3D5

// Simple spinlock type
typedef volatile uint32_t spinlock_t;
#define SPINLOCK_INIT 0

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

// Global spinlock for VGA access
static spinlock_t vga_lock = SPINLOCK_INIT;

// Low-level port I/O functions
static inline void outb(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

// Spinlock functions
static inline void spin_lock(spinlock_t* lock) {
    while (__sync_lock_test_and_set(lock, 1)) {
        __asm__ volatile ("pause");
    }
}

static inline void spin_unlock(spinlock_t* lock) {
    __sync_lock_release(lock);
}

// Update hardware cursor position
static inline void update_cursor(void) {
    uint16_t pos = cursor_y * VGA_WIDTH + cursor_x;
    
    outb(VGA_CTRL_PORT, 14);
    outb(VGA_DATA_PORT, (pos >> 8) & 0xFF);
    outb(VGA_CTRL_PORT, 15);
    outb(VGA_DATA_PORT, pos & 0xFF);
}

// Scroll the screen up one line
static inline void scroll(void) {
    // Move all lines up
    for (size_t i = 0; i < VGA_SIZE - VGA_WIDTH; i++) {
        VGA_BUFFER[i] = VGA_BUFFER[i + VGA_WIDTH];
    }
    
    // Clear the last line
    for (size_t i = VGA_SIZE - VGA_WIDTH; i < VGA_SIZE; i++) {
        VGA_BUFFER[i].character = ' ';
        VGA_BUFFER[i].color = vga_entry(0, VGA_LIGHT_GREY, VGA_BLACK) >> 8;
    }
    
    cursor_y--;
}

// Create a VGA entry
static inline uint16_t vga_entry(char c, uint8_t fg, uint8_t bg) {
    return (uint16_t)c | ((uint16_t)((bg << 4) | (fg & 0x0F)) << 8);
}

// Clear the screen
static inline void vga_clear(void) {
    spin_lock(&vga_lock);
    
    for (size_t i = 0; i < VGA_SIZE; i++) {
        VGA_BUFFER[i].character = ' ';
        VGA_BUFFER[i].color = vga_entry(0, VGA_LIGHT_GREY, VGA_BLACK) >> 8;
    }
    cursor_x = cursor_y = 0;
    update_cursor();
    
    spin_unlock(&vga_lock);
}

// Set cursor position
static inline void vga_set_cursor(uint8_t x, uint8_t y) {
    spin_lock(&vga_lock);
    
    if (x >= VGA_WIDTH) x = VGA_WIDTH - 1;
    if (y >= VGA_HEIGHT) y = VGA_HEIGHT - 1;
    
    cursor_x = x;
    cursor_y = y;
    update_cursor();
    
    spin_unlock(&vga_lock);
}

// Write a character to the current cursor position
static inline void vga_putchar(char c, uint8_t fg, uint8_t bg) {
    spin_lock(&vga_lock);
    
    if (c == '\n') {
        cursor_x = 0;
        if (++cursor_y >= VGA_HEIGHT) {
            scroll();
        }
    } else {
        size_t index = cursor_y * VGA_WIDTH + cursor_x;
        VGA_BUFFER[index].character = c;
        VGA_BUFFER[index].color = ((bg << 4) | (fg & 0x0F));
        
        if (++cursor_x >= VGA_WIDTH) {
            cursor_x = 0;
            if (++cursor_y >= VGA_HEIGHT) {
                scroll();
            }
        }
    }
    
    update_cursor();
    spin_unlock(&vga_lock);
}

// Write a string to the current cursor position
static inline void vga_puts(const char* str, uint8_t fg, uint8_t bg) {
    spin_lock(&vga_lock);
    
    while (*str) {
        if (*str == '\n') {
            cursor_x = 0;
            if (++cursor_y >= VGA_HEIGHT) {
                scroll();
            }
        } else {
            size_t index = cursor_y * VGA_WIDTH + cursor_x;
            VGA_BUFFER[index].character = *str;
            VGA_BUFFER[index].color = ((bg << 4) | (fg & 0x0F));
            
            if (++cursor_x >= VGA_WIDTH) {
                cursor_x = 0;
                if (++cursor_y >= VGA_HEIGHT) {
                    scroll();
                }
            }
        }
        str++;
    }
    
    update_cursor();
    spin_unlock(&vga_lock);
}

// Get current cursor position
static inline void vga_get_cursor(uint8_t* x, uint8_t* y) {
    spin_lock(&vga_lock);
    *x = cursor_x;
    *y = cursor_y;
    spin_unlock(&vga_lock);
}

#endif // VGA_H
