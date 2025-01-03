// SystemKernel.hpp
#pragma once
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_spiffs.h"
#include "esp_vfs.h"
#include "esp_vfs_fat.h"
#include "nvs_flash.h"
#include "esp_event.h"
#include "esp_log.h"
#include <memory>
#include <vector>

class SystemKernel {
public:
    static SystemKernel& getInstance() {
        static SystemKernel instance;
        return instance;
    }

    bool init() {
        ESP_LOGI(TAG, "Initializing system kernel...");
        
        // Initialize NVS
        esp_err_t ret = nvs_flash_init();
        if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
            ESP_ERROR_CHECK(nvs_flash_erase());
            ret = nvs_flash_init();
        }
        ESP_ERROR_CHECK(ret);

        // Initialize event loop
        ESP_ERROR_CHECK(esp_event_loop_create_default());

        // Mount SPIFFS
        if (!initSPIFFS()) {
            ESP_LOGE(TAG, "SPIFFS mount failed");
            return false;
        }

        // Mount SD Card
        if (!initSDCard()) {
            ESP_LOGE(TAG, "SD Card mount failed");
            return false;
        }

        // Initialize task scheduler
        initTaskScheduler();

        ESP_LOGI(TAG, "System kernel initialized successfully");
        return true;
    }

    // File system paths
    static constexpr const char* SPIFFS_BASE_PATH = "/spiffs";
    static constexpr const char* SD_BASE_PATH = "/sdcard";
    static constexpr const char* MODEL_PATH = "/sdcard/models";
    static constexpr const char* DATA_PATH = "/sdcard/data";

    // Task management
    TaskHandle_t createTask(TaskFunction_t task, const char* name, 
                          uint32_t stackSize, void* params, 
                          UBaseType_t priority) {
        TaskHandle_t handle;
        BaseType_t result = xTaskCreate(
            task,
            name,
            stackSize,
            params,
            priority,
            &handle
        );
        
        if (result == pdPASS) {
            taskHandles.push_back(handle);
            return handle;
        }
        return nullptr;
    }

    void suspendTask(TaskHandle_t handle) {
        vTaskSuspend(handle);
    }

    void resumeTask(TaskHandle_t handle) {
        vTaskResume(handle);
    }

private:
    static constexpr const char* TAG = "SystemKernel";
    std::vector<TaskHandle_t> taskHandles;

    SystemKernel() {} // Private constructor for singleton

    bool initSPIFFS() {
        esp_vfs_spiffs_conf_t conf = {
            .base_path = SPIFFS_BASE_PATH,
            .partition_label = nullptr,
            .max_files = 5,
            .format_if_mount_failed = true
        };

        esp_err_t ret = esp_vfs_spiffs_register(&conf);
        if (ret != ESP_OK) {
            if (ret == ESP_FAIL) {
                ESP_LOGE(TAG, "Failed to mount SPIFFS");
            } else if (ret == ESP_ERR_NOT_FOUND) {
                ESP_LOGE(TAG, "Failed to find SPIFFS partition");
            }
            return false;
        }

        size_t total = 0, used = 0;
        ret = esp_spiffs_info(nullptr, &total, &used);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to get SPIFFS partition information");
            return false;
        }

        ESP_LOGI(TAG, "SPIFFS Partition: total: %d, used: %d", total, used);
        return true;
    }

    bool initSDCard() {
        esp_vfs_fat_sdmmc_mount_config_t mount_config = {
            .format_if_mount_failed = false,
            .max_files = 5,
            .allocation_unit_size = 16 * 1024
        };

        sdmmc_card_t* card;
        const char mount_point[] = SD_BASE_PATH;
        
        ESP_LOGI(TAG, "Initializing SD card");

        // Initialize SPI bus for SD card
        spi_bus_config_t bus_cfg = {
            .mosi_io_num = CONFIG_SD_MOSI,
            .miso_io_num = CONFIG_SD_MISO,
            .sclk_io_num = CONFIG_SD_SCK,
            .quadwp_io_num = -1,
            .quadhd_io_num = -1,
            .max_transfer_sz = 4000,
        };

        sdmmc_host_t host = SDSPI_HOST_DEFAULT();
        spi_bus_initialize(host.slot, &bus_cfg, SDSPI_DEFAULT_DMA);

        sdspi_device_config_t slot_config = SDSPI_DEVICE_CONFIG_DEFAULT();
        slot_config.gpio_cs = CONFIG_SD_CS;
        slot_config.host_id = host.slot;

        esp_err_t ret = esp_vfs_fat_sdspi_mount(mount_point, &host, &slot_config, 
                                               &mount_config, &card);

        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to mount SD card SPIFFS");
            return false;
        }

        // Create necessary directories
        mkdir(MODEL_PATH, 0755);
        mkdir(DATA_PATH, 0755);

        return true;
    }

    void initTaskScheduler() {
        // Initialize system monitoring task
        createTask(systemMonitorTask, "SysMonitor", 2048, nullptr, 1);
        
        // Initialize memory management task
        createTask(memoryManagerTask, "MemManager", 2048, nullptr, 2);
    }

    static void systemMonitorTask(void* parameters) {
        while(1) {
            // Monitor system health
            ESP_LOGI(TAG, "Free heap: %lu", esp_get_free_heap_size());
            ESP_LOGI(TAG, "Min free heap: %lu", esp_get_minimum_free_heap_size());
            
            // Check task states
            char* taskList = (char*)malloc(2048);
            if (taskList) {
                vTaskList(taskList);
                ESP_LOGI(TAG, "Task List:\n%s", taskList);
                free(taskList);
            }
            
            vTaskDelay(pdMS_TO_TICKS(10000)); // 10 second intervals
        }
    }

    static void memoryManagerTask(void* parameters) {
        while(1) {
            // Monitor heap fragmentation
            if (esp_get_free_heap_size() < 10000) {  // Example threshold
                ESP_LOGW(TAG, "Low memory condition detected");
                // Trigger cleanup routines
            }
            
            vTaskDelay(pdMS_TO_TICKS(5000)); // 5 second intervals
        }
    }
};
