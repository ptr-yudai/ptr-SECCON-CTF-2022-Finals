#include <iostream>
#include <iomanip>
#include <vector>

class RC4 {
public:
  RC4(const std::string &key) {
    _S.resize(0x100);
    for (int i = 0; i < 0x100; i++) {
      _S[i] = (unsigned char)i;
    }
    unsigned char j = 0;
    for (int i = 0; i < 0x100; i++) {
      j += _S[i] + key[i % key.size()];
      std::swap(_S.at(i), _S.at(j));
    }
  }

  unsigned char* encrypt(const std::string &s) {
    unsigned char i = 0, j = 0;
    unsigned char* o = new unsigned char[s.size()];

    for (int n = 0; n < s.size(); n++) {
      i += 1;
      j += _S[i];
      std::swap(_S.at(i), _S.at(j));
      o[n] = _S[(_S[i] + _S[j]) % 0x100] ^ s[n];
    }

    return o;
  }

private:
  std::vector<unsigned char> _S;
};

int main() {
  std::string key, plain;
  std::cout << "Key: ";
  std::cin >> key;

  std::cout << "Plaintext: ";
  std::cin >> plain;

  RC4 rc4(key);
  std::cout << "Ciphertext: ";
  std::cout << std::hex << std::setfill('0');
  unsigned char* cipher = rc4.encrypt(plain);
  for (int i = 0; i < plain.size(); i++) {
    std::cout << std::setw(2) << static_cast<unsigned>(cipher[i]);
  }
  std::cout << std::endl;

  delete cipher;
  return 0;
}
