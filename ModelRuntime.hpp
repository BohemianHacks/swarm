// ModelRuntime.hpp
#pragma once
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include <map>
#include <string>

// Model states
enum class ModelState {
    UNLOADED,
    LOADING,
    READY,
    RUNNING,
    ERROR
};

// Model request types
enum class ModelOp {
    LOAD,
    UNLOAD,
    RUN,
    STATUS
};

struct ModelRequest {
    ModelOp operation;
    std::string modelId;
    uint8_t* inputData;
    size_t inputLength;
    uint32_t requestId;
};

struct ModelResponse {
    bool success;
    std::string message;
    uint8_t* outputData;
    size_t outputLength;
    uint32_t requestId;
    ModelState state;
};

class ModelRuntime {
public:
    ModelRuntime(size_t queueSize = 5) {
        requestQueue = xQueueCreate(queueSize, sizeof(ModelRequest));
        responseQueue = xQueueCreate(queueSize, sizeof(ModelResponse));
        modelMutex = xSemaphoreCreateMutex();
        
        xTaskCreate(
            modelTaskWrapper,
            "ModelTask",
            16384, // Larger stack for ML operations
            this,
            5,
            &modelTaskHandle
        );
    }

    // Async model loading request
    bool requestModelLoad(const std::string& modelId, uint32_t requestId) {
        ModelRequest request = {
            .operation = ModelOp::LOAD,
            .modelId = modelId,
            .inputData = nullptr,
            .inputLength = 0,
            .requestId = requestId
        };
        return xQueueSend(requestQueue, &request, portMAX_DELAY) == pdTRUE;
    }

    // Async inference request
    bool requestInference(const std::string& modelId, uint8_t* inputData, 
                         size_t inputLength, uint32_t requestId) {
        ModelRequest request = {
            .operation = ModelOp::RUN,
            .modelId = modelId,
            .inputData = inputData,
            .inputLength = inputLength,
            .requestId = requestId
        };
        return xQueueSend(requestQueue, &request, portMAX_DELAY) == pdTRUE;
    }

    // Get response from model operations
    bool getResponse(ModelResponse& response, TickType_t timeout = portMAX_DELAY) {
        return xQueueReceive(responseQueue, &response, timeout) == pdTRUE;
    }

private:
    struct ModelContext {
        std::unique_ptr<tflite::MicroInterpreter> interpreter;
        std::unique_ptr<tflite::MicroMutableOpResolver<10>> resolver;
        const tflite::Model* model;
        uint8_t* tensorArena;
        size_t tensorArenaSize;
        ModelState state;
    };

    QueueHandle_t requestQueue;
    QueueHandle_t responseQueue;
    SemaphoreHandle_t modelMutex;
    TaskHandle_t modelTaskHandle;
    std::map<std::string, ModelContext> loadedModels;

    static void modelTaskWrapper(void* params) {
        static_cast<ModelRuntime*>(params)->modelTask();
    }

    void modelTask() {
        ModelRequest request;
        ModelResponse response;

        while (true) {
            if (xQueueReceive(requestQueue, &request, portMAX_DELAY) == pdTRUE) {
                if (xSemaphoreTake(modelMutex, portMAX_DELAY) == pdTRUE) {
                    switch (request.operation) {
                        case ModelOp::LOAD:
                            handleModelLoad(request, response);
                            break;
                        case ModelOp::RUN:
                            handleInference(request, response);
                            break;
                        case ModelOp::UNLOAD:
                            handleModelUnload(request, response);
                            break;
                    }
                    xSemaphoreGive(modelMutex);
                }
                xQueueSend(responseQueue, &response, portMAX_DELAY);
            }
        }
    }

    void handleModelLoad(const ModelRequest& request, ModelResponse& response) {
        // Check if model is already loaded
        if (loadedModels.find(request.modelId) != loadedModels.end()) {
            response = {
                .success = true,
                .message = "Model already loaded",
                .outputData = nullptr,
                .outputLength = 0,
                .requestId = request.requestId,
                .state = ModelState::READY
            };
            return;
        }

        try {
            ModelContext context;
            context.state = ModelState::LOADING;
            
            // Load model from filesystem (implementation depends on storage system)
            context.model = loadModelFromStorage(request.modelId);
            if (!context.model) throw std::runtime_error("Failed to load model file");

            // Setup TFLite micro
            context.resolver = std::make_unique<tflite::MicroMutableOpResolver<10>>();
            setupOperators(*context.resolver);

            // Allocate tensor arena
            context.tensorArenaSize = 32 * 1024; // Adjust based on model needs
            context.tensorArena = new uint8_t[context.tensorArenaSize];

            // Create interpreter
            context.interpreter = std::make_unique<tflite::MicroInterpreter>(
                context.model, *context.resolver,
                context.tensorArena, context.tensorArenaSize
            );

            if (context.interpreter->AllocateTensors() != kTfLiteOk) {
                throw std::runtime_error("Failed to allocate tensors");
            }

            context.state = ModelState::READY;
            loadedModels[request.modelId] = std::move(context);

            response = {
                .success = true,
                .message = "Model loaded successfully",
                .outputData = nullptr,
                .outputLength = 0,
                .requestId = request.requestId,
                .state = ModelState::READY
            };
        } catch (const std::exception& e) {
            response = {
                .success = false,
                .message = e.what(),
                .outputData = nullptr,
                .outputLength = 0,
                .requestId = request.requestId,
                .state = ModelState::ERROR
            };
        }
    }

    void handleInference(const ModelRequest& request, ModelResponse& response) {
        auto modelIt = loadedModels.find(request.modelId);
        if (modelIt == loadedModels.end()) {
            response = {
                .success = false,
                .message = "Model not loaded",
                .outputData = nullptr,
                .outputLength = 0,
                .requestId = request.requestId,
                .state = ModelState::UNLOADED
            };
            return;
        }

        try {
            auto& context = modelIt->second;
            context.state = ModelState::RUNNING;

            // Copy input data to input tensor
            auto* inputTensor = context.interpreter->input(0);
            memcpy(inputTensor->data.raw, request.inputData, request.inputLength);

            // Run inference
            if (context.interpreter->Invoke() != kTfLiteOk) {
                throw std::runtime_error("Inference failed");
            }

            // Get output
            auto* outputTensor = context.interpreter->output(0);
            uint8_t* outputData = new uint8_t[outputTensor->bytes];
            memcpy(outputData, outputTensor->data.raw, outputTensor->bytes);

            context.state = ModelState::READY;
            response = {
                .success = true,
                .message = "Inference successful",
                .outputData = outputData,
                .outputLength = outputTensor->bytes,
                .requestId = request.requestId,
                .state = ModelState::READY
            };
        } catch (const std::exception& e) {
            response = {
                .success = false,
                .message = e.what(),
                .outputData = nullptr,
                .outputLength = 0,
                .requestId = request.requestId,
                .state = ModelState::ERROR
            };
        }
    }

private:
    // Helper methods
    const tflite::Model* loadModelFromStorage(const std::string& modelId) {
        // Implementation depends on your storage system
        // Return nullptr if loading fails
        return nullptr;
    }

    void setupOperators(tflite::MicroMutableOpResolver<10>& resolver) {
        // Add required operators for your models
        resolver.AddFullyConnected();
        resolver.AddConv2D();
        resolver.AddMaxPool2D();
        // Add more operators as needed
    }
};
