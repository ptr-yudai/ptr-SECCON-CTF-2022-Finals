#include "pico/stdlib.h"
#include "hardware/pwm.h"

#define PIN_LED  PICO_DEFAULT_LED_PIN
#define PIN_ROW1 0
#define PIN_ROW2 1
#define PIN_ROW3 2
#define PIN_ROW4 3
#define PIN_COL1 4
#define PIN_COL2 5
#define PIN_COL3 6
#define PIN_COL4 7
#define PIN_SND  8
#define PIN_MOTOR 9

void set_frequency(pwm_config *config, uint slice, uint freq) {
  uint count = 125000000 * 16 / freq;
  uint div = count / 60000;
  config->div = div;
  config->top = count / div;
  pwm_init(slice, config, true);
  pwm_set_chan_level(slice, PWM_CHAN_A, config->top / 2);
}

void init_gpio(pwm_config *config, uint slice) {
  gpio_init(PIN_LED);
  gpio_set_dir(PIN_LED, GPIO_OUT);
  gpio_set_dir(PIN_MOTOR, GPIO_OUT);
  gpio_init_mask         (0b1111111111);
  gpio_set_dir_in_masked (0b0011111111);
  gpio_set_dir_out_masked(0b1100000000);
  for (uint pin = PIN_ROW1; pin <= PIN_COL4; pin++)
    gpio_pull_down(pin);

  /* Setup PWM */
  gpio_set_function(PIN_SND, GPIO_FUNC_PWM);
  *config = pwm_get_default_config();
  pwm_set_chan_level(slice, PWM_CHAN_A, 0);
  pwm_set_enabled(slice, false);
}

void play_error(pwm_config *config, uint slice) {
  set_frequency(config, slice, 440);
  for (int i = 0; i < 3; i++) {
    pwm_set_enabled(slice, true);
    sleep_ms(250);
    pwm_set_enabled(slice, false);
    sleep_ms(250);
  }
}

void play_ok(pwm_config *config, uint slice) {
  pwm_set_enabled(slice, true);
  set_frequency(config, slice, 494);
  sleep_ms(100);
  set_frequency(config, slice, 587);
  sleep_ms(100);
  set_frequency(config, slice, 784);
  sleep_ms(100);
  pwm_set_enabled(slice, false);
}

void play_click(pwm_config *config, uint slice) {
  set_frequency(config, slice, 1000);
  pwm_set_enabled(slice, true);
  sleep_ms(100);
  pwm_set_enabled(slice, false);
}

void unlock_door(pwm_config *config, uint slice, uint slot[16]) {
  uint x = 0, v = 777;
  for (uint i = 0; i < 16; i++) {
    x |= slot[i] - (v & 0xf);
    if (v % 2 == 0) {
      v >>= 1;
    } else {
      v = v * 3 + 1;
    }
  }
  if (x == 0) {
    play_ok(config, slice);
    gpio_put(PIN_MOTOR, 1);
    sleep_ms(5000);
    gpio_put(PIN_MOTOR, 0);
  } else {
    play_error(config, slice);
  }
}

int check_button_state(uint state, bool prev[16]) {
  int j;
  bool row1, row2, row3, row4, col1, col2, col3, col4;
  row1 = (state >> PIN_ROW1) & 1;
  row2 = (state >> PIN_ROW2) & 1;
  row3 = (state >> PIN_ROW3) & 1;
  row4 = (state >> PIN_ROW4) & 1;
  col1 = (state >> PIN_COL1) & 1;
  col2 = (state >> PIN_COL2) & 1;
  col3 = (state >> PIN_COL3) & 1;
  col4 = (state >> PIN_COL4) & 1;
  bool check[16] = {
    row4 & col1, row1 & col1, row1 & col2, row1 & col3,
    row2 & col1, row2 & col2, row2 & col3, row3 & col1,
    row3 & col2, row3 & col3, row1 & col4, row2 & col4,
    row3 & col4, row4 & col4, row4 & col3, row4 & col2,
  };
  uint table[16] = {
    15, 3, 10, 1, 4, 5, 12, 13, 9, 2, 6, 11, 8, 7, 14, 0
  };

  for (j = 0; j < 16; j++) {
    if (!prev[j] && check[j]) {
      prev[j] = true;
      return table[j];
    } else if (!check[j]) {
      prev[j] = false;
    }
  }

  return -1;
}

int main() {
  uint i, slice, state, slot[16], slot_pos = 0;
  int n;
  pwm_config config;
  bool prev_state[16];

  for (i = 0; i < 16; i++)
    prev_state[i] = false;

  slice = pwm_gpio_to_slice_num(PIN_SND);
  init_gpio(&config, slice);

  i = 0;
  while (true) {
    state = gpio_get_all();
    n = check_button_state(state, prev_state);
    if (n != -1) {
      play_click(&config, slice);
      sleep_ms(100);
      slot[slot_pos] = n;
      slot_pos++;
      if (slot_pos == 16) {
        unlock_door(&config, slice, slot);
        slot_pos = 0;
      }
    }

    sleep_ms(1);

    i = (i + 1) % 1000;
    if (i == 0)
      gpio_put(PIN_LED, 0);
    else if (i == 500)
      gpio_put(PIN_LED, 1);
  }
}
