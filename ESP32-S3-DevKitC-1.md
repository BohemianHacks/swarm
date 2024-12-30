## ESP32-S3-DevKitC-1 build configuration:
- The ESP32-S3-DevKitC-1 has 8MB flash and 8MB PSRAM
- The default UART port is through USB-C (no external USB-UART bridge needed)
- GPIO19/20 are used for USB communication
- The board supports both 802.11b/g/n Wi-Fi and Bluetooth 5 (LE)


```ini
CONFIG_IDF_TARGET="esp32s3"
CONFIG_IDF_TARGET_ESP32S3=y
CONFIG_ESPTOOLPY_FLASHMODE_QIO=y
CONFIG_ESPTOOLPY_FLASHSIZE_8MB=y
CONFIG_ESPTOOLPY_FLASHFREQ_80M=y
CONFIG_ESP32S3_DEFAULT_CPU_FREQ_240=y
CONFIG_ESP32S3_SPIRAM_SUPPORT=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y

# Enable Wi-Fi
CONFIG_ESP_WIFI_STATIC_RX_BUFFER_NUM=16
CONFIG_ESP_WIFI_DYNAMIC_RX_BUFFER_NUM=32
CONFIG_ESP_WIFI_DYNAMIC_TX_BUFFER_NUM=32
CONFIG_ESP_WIFI_AMPDU_TX_ENABLED=y
CONFIG_ESP_WIFI_TX_BA_WIN=6
CONFIG_ESP_WIFI_RX_BA_WIN=6

# Enable FreeRTOS optimization
CONFIG_FREERTOS_HZ=1000
CONFIG_FREERTOS_USE_TICKLESS_IDLE=y

# Memory optimization for TensorFlow
CONFIG_ESP32S3_INSTRUCTION_CACHE_32KB=y
CONFIG_ESP32S3_DATA_CACHE_64KB=y
CONFIG_ESP32S3_DATA_CACHE_LINE_64B=y
CONFIG_ESP_INT_WDT=y
CONFIG_ESP_TASK_WDT=y

```

```cmake
# main/CMakeLists.txt
idf_component_register(
    SRCS "swarm_node.cpp"
    INCLUDE_DIRS "."
    REQUIRES esp_wifi nvs_flash esp_timer tensorflow-lite-esp32
)

target_compile_options(${COMPONENT_LIB} PRIVATE -std=gnu++17)

```

To get started:

1. First, install ESP-IDF v5.0 or later if you haven't already:
```bash
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh
. ./export.sh
```

2. Create your project structure:
```bash
mkdir swarm_intelligence && cd swarm_intelligence
# Copy the CMakeLists.txt files and sdkconfig shown above
mkdir -p main
# Copy your swarm_node.cpp to main/
```

3. Install TensorFlow dependencies:
```bash
cd components
git clone --recursive https://github.com/espressif/tflite-micro-esp-examples
mv tflite-micro-esp-examples/components/tensorflow tensorflow
rm -rf tflite-micro-esp-examples
```

4. Configure and build:
```bash
idf.py set-target esp32s3
idf.py menuconfig  # Optional: You can verify/adjust the settings
idf.py build
```

5. Flash (replace /dev/ttyUSB0 with your port):
```bash
idf.py -p /dev/ttyUSB0 flash monitor
```
