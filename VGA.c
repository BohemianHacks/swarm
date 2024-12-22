#include <stdio.h>

/**
 * Prints the contents of the VGA text buffer to the console.
 * The VGA text buffer is located at memory address 0xB8000 and uses
 * a 2-byte format for each character (char byte + attribute byte).
 * Screen dimensions are 80x25 characters in text mode.
 */
void print_vga_buffer() {
    // Point to the start of the VGA text buffer
    unsigned char* vga_buffer = (unsigned char*)0xB8000;
    
    // Constants for VGA text mode
    const int SCREEN_WIDTH = 80;
    const int SCREEN_HEIGHT = 25;
    const int BYTES_PER_CHAR = 2;
    const int BUFFER_SIZE = SCREEN_WIDTH * SCREEN_HEIGHT * BYTES_PER_CHAR;
    
    // ASCII range for printable characters
    const int ASCII_PRINTABLE_START = 32;
    const int ASCII_PRINTABLE_END = 126;

    // Iterate through the buffer, processing 2 bytes at a time
    for (int i = 0; i < BUFFER_SIZE; i += BYTES_PER_CHAR) {
        // Extract character and its attribute
        char character = vga_buffer[i];
        char attribute = vga_buffer[i + 1];

        // Print either the character or a dot if non-printable
        if (character >= ASCII_PRINTABLE_START && 
            character <= ASCII_PRINTABLE_END) {
            putchar(character);
        } else {
            putchar('.');
        }

        // Add newline at the end of each row
        if ((i / BYTES_PER_CHAR + 1) % SCREEN_WIDTH == 0) {
            printf("\n");
        }
    }
}

/**
 * Main entry point of the program.
 * Calls the VGA buffer printing function and returns.
 *
 * @return 0 on successful execution
 */
int main() {
    print_vga_buffer();
    return 0;
}
