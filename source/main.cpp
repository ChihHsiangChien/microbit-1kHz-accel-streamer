#include "MicroBit.h"
#include "FastUARTService.h"

using namespace codal;

MicroBit uBit;
FastUARTService *uart;

uint8_t sensor_addr = 0; 
bool is_qma = false;
uint8_t scale_gs[] = {2, 4, 8, 16};
int current_scale_idx = 2; 

void update_sensor_scale() {
    if (sensor_addr == 0x32) { // LSM303
        uint8_t reg23[] = {0x23, (uint8_t)(0x80 | (current_scale_idx << 4))}; 
        uBit._i2c.write(sensor_addr, reg23, 2);
    } 
    else if (sensor_addr == 0x24 || sensor_addr == 0x26) { // QMA6100
        uint8_t range_val = (current_scale_idx == 0) ? 0x01 : (current_scale_idx == 1) ? 0x02 : (current_scale_idx == 2) ? 0x04 : 0x08;
        uint8_t range[] = {0x0F, range_val}; uBit._i2c.write(sensor_addr, range, 2);
    }
    // 第一排顯示當前量程 (1-4個點)
    for(int i=0; i<5; i++) uBit.display.image.setPixelValue(i, 0, (i <= current_scale_idx) ? 255 : 0);
}

int main() {
    uBit.init();
    
    uBit._i2c.setFrequency(400000); 

    // Scan for sensor
    uint8_t scan_reg = 0x00;
    if (uBit._i2c.write(0x32, &scan_reg, 1, true) == DEVICE_OK) sensor_addr = 0x32;
    else if (uBit._i2c.write(0x24, &scan_reg, 1, true) == DEVICE_OK) sensor_addr = 0x24;
    else if (uBit._i2c.write(0x26, &scan_reg, 1, true) == DEVICE_OK) sensor_addr = 0x26;

    if (sensor_addr == 0x24 || sensor_addr == 0x26) is_qma = true;

    if (!is_qma) {
        uint8_t reg20[] = {0x20, 0x97}; uBit._i2c.write(sensor_addr, reg20, 2);
    } else {
        uint8_t reset[] = {0x11, 0x80}; uBit._i2c.write(sensor_addr, reset, 2);
        uBit.sleep(20);
        uint8_t mode[] = {0x11, 0x01}; uBit._i2c.write(sensor_addr, mode, 2);
    }
    update_sensor_scale();

    if(uBit.ble) {
        uBit.bleManager.init(ManagedString("VBT_ULTRA"), ManagedString("1"), uBit.messageBus, uBit.storage, false);
        uBit.bleManager.advertise();
    }
    uart = new FastUARTService(*uBit.ble, 2048, 2048);

    uint32_t global_sample_index = 0;
    uint8_t packet[128]; 
    int packed_samples = 0;
    int dot_x = 0;
    bool last_btn_a = false;

    while(1) {
        uint64_t start_loop = uBit.systemTime();

        // 每 100ms 處理低速任務
        if (global_sample_index % 100 == 0) {
            bool btn_a = uBit.buttonA.isPressed();
            if (btn_a && !last_btn_a) {
                current_scale_idx = (current_scale_idx + 1) % 4;
                update_sensor_scale();
            }
            last_btn_a = btn_a;
            fiber_sleep(1); 
        }

        uint8_t accel_raw[6] = {0,0,0,0,0,0};
        if (sensor_addr != 0) {
            uint8_t cmd = is_qma ? 0x01 : 0xA8;
            uBit._i2c.write(sensor_addr, &cmd, 1, true);
            uBit._i2c.read(sensor_addr, accel_raw, 6);
        }

        int offset = packed_samples * 6;
        packet[offset] = accel_raw[1]; packet[offset+1] = accel_raw[0];
        packet[offset+2] = accel_raw[3]; packet[offset+3] = accel_raw[2];
        packet[offset+4] = accel_raw[5]; packet[offset+5] = accel_raw[4];

        if (++packed_samples >= 20) {
            packet[120] = scale_gs[current_scale_idx];
            packet[124] = (global_sample_index >> 24) & 0xFF;
            packet[125] = (global_sample_index >> 16) & 0xFF;
            packet[126] = (global_sample_index >> 8) & 0xFF;
            packet[127] = global_sample_index & 0xFF;
            if (uBit.ble->getConnected()) uart->send(packet, 128, ASYNC);
            packed_samples = 0;
            
            // 心跳
            uBit.display.image.setPixelValue(dot_x, 4, 0);
            dot_x = (dot_x + 1) % 5;
            uBit.display.image.setPixelValue(dot_x, 4, 255);
        }
        global_sample_index++;

        // 緊密計時
        while ((uBit.systemTime() - start_loop) < 1);
    }
}
