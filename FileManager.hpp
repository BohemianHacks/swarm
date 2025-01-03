// FileManager.hpp
#pragma once
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_spiffs.h"
#include <string>

// File operation request types
enum class FileOp {
    READ,
    WRITE,
    DELETE,
    LIST,
    STATUS
};

// Request structure for file operations
struct FileRequest {
    FileOp operation;
    std::string filename;
    uint8_t* data;
    size_t length;
    uint32_t requestId;
};

// Response structure for file operations
struct FileResponse {
    bool success;
    std::string message;
    uint8_t* data;
    size_t length;
    uint32_t requestId;
};

class FileManager {
public:
    FileManager(size_t queueSize = 10) {
        // Create queues for requests and responses
        requestQueue = xQueueCreate(queueSize, sizeof(FileRequest));
        responseQueue = xQueueCreate(queueSize, sizeof(FileResponse));
        
        // Create mutex for file operations
        fileMutex = xSemaphoreCreateMutex();
        
        // Create file I/O task
        xTaskCreate(
            fileTaskWrapper,
            "FileTask",
            8192,
            this,
            5,
            &fileTaskHandle
        );
    }

    // Async file read request
    bool requestRead(const std::string& filename, uint32_t requestId) {
        FileRequest request = {
            .operation = FileOp::READ,
            .filename = filename,
            .data = nullptr,
            .length = 0,
            .requestId = requestId
        };
        return xQueueSend(requestQueue, &request, portMAX_DELAY) == pdTRUE;
    }

    // Async file write request
    bool requestWrite(const std::string& filename, uint8_t* data, size_t length, uint32_t requestId) {
        FileRequest request = {
            .operation = FileOp::WRITE,
            .filename = filename,
            .data = data,
            .length = length,
            .requestId = requestId
        };
        return xQueueSend(requestQueue, &request, portMAX_DELAY) == pdTRUE;
    }

    // Get response from file operations
    bool getResponse(FileResponse& response, TickType_t timeout = portMAX_DELAY) {
        return xQueueReceive(responseQueue, &response, timeout) == pdTRUE;
    }

private:
    QueueHandle_t requestQueue;
    QueueHandle_t responseQueue;
    SemaphoreHandle_t fileMutex;
    TaskHandle_t fileTaskHandle;

    // Wrapper for task creation
    static void fileTaskWrapper(void* params) {
        static_cast<FileManager*>(params)->fileTask();
    }

    // Main file I/O task
    void fileTask() {
        FileRequest request;
        FileResponse response;

        while (true) {
            if (xQueueReceive(requestQueue, &request, portMAX_DELAY) == pdTRUE) {
                // Take mutex for file operation
                if (xSemaphoreTake(fileMutex, portMAX_DELAY) == pdTRUE) {
                    switch (request.operation) {
                        case FileOp::READ:
                            handleRead(request, response);
                            break;
                        case FileOp::WRITE:
                            handleWrite(request, response);
                            break;
                        // Add other operations as needed
                    }
                    xSemaphoreGive(fileMutex);
                }
                
                // Send response
                xQueueSend(responseQueue, &response, portMAX_DELAY);
            }
        }
    }

    // Handle file read operation
    void handleRead(const FileRequest& request, FileResponse& response) {
        FILE* file = fopen(request.filename.c_str(), "rb");
        if (file == nullptr) {
            response = {
                .success = false,
                .message = "Failed to open file",
                .data = nullptr,
                .length = 0,
                .requestId = request.requestId
            };
            return;
        }

        // Get file size
        fseek(file, 0, SEEK_END);
        size_t size = ftell(file);
        fseek(file, 0, SEEK_SET);

        // Allocate buffer and read file
        uint8_t* buffer = new uint8_t[size];
        size_t read = fread(buffer, 1, size, file);
        fclose(file);

        response = {
            .success = (read == size),
            .message = (read == size) ? "Success" : "Read error",
            .data = buffer,
            .length = read,
            .requestId = request.requestId
        };
    }

    // Handle file write operation
    void handleWrite(const FileRequest& request, FileResponse& response) {
        FILE* file = fopen(request.filename.c_str(), "wb");
        if (file == nullptr) {
            response = {
                .success = false,
                .message = "Failed to create file",
                .data = nullptr,
                .length = 0,
                .requestId = request.requestId
            };
            return;
        }

        size_t written = fwrite(request.data, 1, request.length, file);
        fclose(file);

        response = {
            .success = (written == request.length),
            .message = (written == request.length) ? "Success" : "Write error",
            .data = nullptr,
            .length = written,
            .requestId = request.requestId
        };
    }
};
